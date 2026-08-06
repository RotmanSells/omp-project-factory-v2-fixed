import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { cleanupRepo, fakePi, git, importTool, seedFactoryRepo, tempRepo, assert, read, writeJson } from './testlib.mjs';

async function prepareCommitRepo() {
  const dir = tempRepo();
  await seedFactoryRepo(dir);
  const runtime = await importTool('./../project/.omp/tools/lib/runtime.ts');
  const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
  const source = read(taskPath);
  const contractHash = runtime.taskContractHash(source);
  const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
  const state = JSON.parse(read(statePath));
  state.current_task.approved_contract_sha256 = contractHash;
  await writeJson(statePath, state);
  const updated = source.replace('approved_contract_sha256: null', `approved_contract_sha256: "${contractHash}"`);
  await fs.writeFile(taskPath, updated, 'utf8');
  await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 2;\n', 'utf8');
  const diffHash = await runtime.diffHash(fakePi(dir));
  const head = git(dir, ['rev-parse', 'HEAD']);
  const branch = git(dir, ['branch', '--show-current']);
  await writeJson(path.join(dir, '.project-factory', 'reports', 'quality-task-01-001-latest.json'), {
    schema_version: 1,
    scope: 'task',
    id: '01-001',
    verdict: 'PASS',
    created_at: new Date().toISOString(),
    branch,
    head,
    base_commit: head,
    diff_hash: diffHash,
    gates: [],
  });
  await writeJson(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'), {
    schema_version: 1,
    task_id: '01-001',
    reviewer_role: 'reviewer',
    verdict: 'approve',
    branch,
    head,
    diff_hash: diffHash,
    created_at: new Date().toISOString(),
    findings: [],
  });
  return dir;
}

async function testStateTransitions() {
  const dir = tempRepo('state-test-');
  git(dir, ['commit', '--allow-empty', '-q', '-m', 'chore: seed head']);
  try {
    const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
    await writeJson(statePath, {
      schema_version: 2,
      project: { phase: 'brief', architecture_version: null },
      current_stage: null,
      current_task: null,
      blocked_by: null,
      history: [],
    });
    const mod = await importTool('./../project/.omp/tools/project_state.ts');
    const pi = fakePi(dir);
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'start design' });
    let state = JSON.parse(read(statePath));
    assert(state.project.phase === 'design_in_progress', 'project phase should advance');
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'blocked_owner_decision', reason: 'need owner' });
    state = JSON.parse(read(statePath));
    assert(state.project.phase === 'blocked_owner_decision', 'project should block');
    await mod.executeProjectState(pi, { action: 'owner_override', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'owner answered' });
    state = JSON.parse(read(statePath));
    assert(state.project.phase === 'design_in_progress', 'owner override should resume');
    let failed = false;
    try {
      await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'roadmap_in_progress', reason: 'illegal jump' });
    } catch {
      failed = true;
    }
    assert(failed, 'invalid project transition must fail');
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'stage', stageId: '01', next: 'planning', reason: 'plan stage' });
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'stage', stageId: '01', next: 'planned', reason: 'stage planned' });
    state = JSON.parse(read(statePath));
    assert(state.current_stage.status === 'planned', 'stage should reach planned');
  } finally {
    cleanupRepo(dir);
  }
}

async function testQualityGateRestrictions() {
  const dir = tempRepo('gate-test-');
  try {
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'skip', scopes: ['task'], enabled: false, command: 'pnpm', args: ['lint'] },
      ],
    });
    const mod = await importTool('./../project/.omp/tools/quality_gate.ts');
    let result = await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    assert(result.details.report.verdict === 'SKIP', 'disabled gate should yield SKIP');
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'escape', scopes: ['task'], enabled: true, cwd: '../..', command: 'pnpm', args: ['lint'] },
      ],
    });
    let failed = false;
    try {
      await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    } catch {
      failed = true;
    }
    assert(failed, 'cwd escape must fail');
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'npx', scopes: ['task'], enabled: true, command: 'npx', args: ['foo'] },
      ],
    });
    failed = false;
    try {
      await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    } catch {
      failed = true;
    }
    assert(failed, 'package-loading executables must fail');
  } finally {
    cleanupRepo(dir);
  }
}

async function testTaskCommitBlocksAndSuccess() {
  const mod = await importTool('./../project/.omp/tools/task_commit.ts');

  {
    const dir = await prepareCommitRepo();
    try {
      git(dir, ['checkout', '-q', 'main']);
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block on protected branch');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.rm(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'));
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block without review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
      let source = read(taskPath).replace('sensitive: false', 'sensitive: true');
      await fs.writeFile(taskPath, source, 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block missing security review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.writeFile(path.join(dir, 'secret.txt'), 'nope\n', 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block unexpected file');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 3;\n', 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block stale quality or review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
      await fs.writeFile(taskPath, read(taskPath).replace('# Scope', '# Scope changed'), 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block modified task contract');
      const state = JSON.parse(read(path.join(dir, 'docs', 'PROJECT_STATE.json')));
      assert(state.current_task.status === 'ready_to_commit', 'failed commit must not mutate state');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'fix(core): wrong message' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block wrong commit message');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const before = git(dir, ['rev-list', '--count', 'HEAD']);
      const result = await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      const after = git(dir, ['rev-list', '--count', 'HEAD']);
      assert(Number(after) === Number(before) + 1, 'successful task commit must create one commit');
      assert(git(dir, ['status', '--porcelain']) === '', 'tree must be clean after successful task commit');
      assert(String(result.content[0].text).includes('Committed 01-001'), 'result should mention committed task');
    } finally {
      cleanupRepo(dir);
    }
  }
}

async function testMissionCommit() {
  const dir = tempRepo('mission-test-');
  try {
    await seedFactoryRepo(dir);
    await fs.writeFile(path.join(dir, '.project-factory', 'github-outbox', 'issue-01.md'), '# Draft\n', 'utf8');
    const mod = await importTool('./../project/.omp/tools/mission_commit.ts');
    let result = await mod.executeMissionCommit(fakePi(dir), { mission: 'prepare_github', message: 'docs(github): update local drafts' });
    assert(String(result.content[0].text).includes('Mission committed prepare_github'), 'mission commit should succeed for outbox');
    await fs.writeFile(path.join(dir, 'src', 'bad.ts'), 'export const bad = true;\n', 'utf8');
    let failed = false;
    try {
      await mod.executeMissionCommit(fakePi(dir), { mission: 'roadmap', message: 'docs(roadmap): update roadmap' });
    } catch {
      failed = true;
    }
    assert(failed, 'mission_commit must block application code');
  } finally {
    cleanupRepo(dir);
  }
}

async function testGitInspect() {
  const dir = tempRepo('inspect-test-');
  try {
    await seedFactoryRepo(dir);
    const mod = await importTool('./../project/.omp/tools/git_inspect.ts');
    const branch = await mod.executeGitInspect(fakePi(dir), { action: 'current_branch' });
    assert(String(branch.content[0].text).startsWith('stage/'), 'git_inspect should report current branch');
  } finally {
    cleanupRepo(dir);
  }
}

async function testScriptsAndPackaging() {
  const dir = tempRepo('install-test-');
  const root = path.resolve('.');
  try {
    execFileSync('bash', ['audit.sh', dir], { cwd: root, stdio: 'pipe' });
    const before = git(dir, ['status', '--porcelain']);
    assert(before === '', 'audit must not mutate repo');
    execFileSync('bash', ['install.sh', dir], { cwd: root, stdio: 'pipe' });
    assert(!existsSync(path.join(dir, '.omp')), 'dry-run must not create files');
    execFileSync('bash', ['install.sh', '--apply', dir], { cwd: root, stdio: 'pipe' });
    assert(existsSync(path.join(dir, '.omp', 'commands', 'design-project.md')), 'apply install must copy commands');
    assert(existsSync(path.join(dir, '.project-factory', 'quality-gates.json')), 'apply install must copy quality gates');
    execFileSync('bash', ['install.sh', '--apply', dir], { cwd: root, stdio: 'pipe' });
    const backups = execFileSync('bash', ['-lc', 'compgen -G "' + dir + '/.omp.backup.*" || true'], { encoding: 'utf8' }).trim();
    assert(backups !== '', 'repeat install should create backup');
  } finally {
    cleanupRepo(dir);
  }
}

await testStateTransitions();
await testQualityGateRestrictions();
await testTaskCommitBlocksAndSuccess();
await testMissionCommit();
await testGitInspect();
await testScriptsAndPackaging();
console.log('[tests] PASS');
