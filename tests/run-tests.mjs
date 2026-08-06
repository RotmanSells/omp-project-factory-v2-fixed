import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { existsSync, symlinkSync } from "node:fs";
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
  await fs.writeFile(taskPath, source.replace('approved_contract_sha256: null', `approved_contract_sha256: "${contractHash}"`), 'utf8');
  await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 2;\n', 'utf8');
  const hash = await runtime.diffHash(fakePi(dir));
  const head = git(dir, ['rev-parse', 'HEAD']);
  const branch = git(dir, ['branch', '--show-current']);
  await writeJson(path.join(dir, '.project-factory', 'reports', 'quality-task-01-001-latest.json'), {
    schema_version: 1, scope: 'task', id: '01-001', verdict: 'PASS', created_at: new Date().toISOString(), branch, head, base_commit: head, diff_hash: hash, gates: [{ name: 'unit', status: 'PASS' }],
  });
  await writeJson(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'), {
    schema_version: 1, task_id: '01-001', reviewer_role: 'reviewer', verdict: 'approve', branch, head, diff_hash: hash, created_at: new Date().toISOString(), findings: [],
  });
  return dir;
}

async function testStateTransitionsAndSequentialWork() {
  const dir = tempRepo('state-test-');
  try {
    const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
    await writeJson(statePath, { schema_version: 2, project: { phase: 'brief', architecture_version: null }, current_stage: null, current_task: null, blocked_by: null, history: [] });
    git(dir, ['add', '.']);
    git(dir, ['commit', '-q', '-m', 'chore: state seed']);
    const mod = await importTool('./../project/.omp/tools/project_state.ts');
    const pi = fakePi(dir);
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'start design' });
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'blocked_owner_decision', reason: 'need owner' });
    let failed = false;
    try { await mod.executeProjectState(pi, { action: 'owner_override', actor: 'Main', scope: 'project', next: 'roadmap_in_progress', reason: 'invalid override' }); } catch { failed = true; }
    assert(failed, 'owner override must not jump to arbitrary state');
    await mod.executeProjectState(pi, { action: 'owner_override', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'owner answered' });

    let state = JSON.parse(read(statePath));
    state.project.phase = 'implementation';
    state.current_stage = { id: '01', status: 'done', readme_path: 'docs/stages/01-README.md' };
    state.current_task = { id: '01-003', stage_id: '01', status: 'done', doc_path: 'docs/stages/tasks/01-003.md', expected_commit: 'feat(core): old', allowed_paths: ['src/**'], reviewers: ['reviewer'], approved_contract_sha256: 'sha256:old', started_head: git(dir, ['rev-parse', 'HEAD']) };
    await writeJson(statePath, state);
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'stage', stageId: '02', next: 'planning', reason: 'next stage' });
    state = JSON.parse(read(statePath));
    assert(state.current_stage.id === '02' && state.current_stage.status === 'planning', 'next stage must replace completed stage');
    assert(state.current_task === null, 'new stage must clear completed current task');

    await fs.mkdir(path.join(dir, 'docs', 'stages', 'tasks'), { recursive: true });
    const task = `---\nid: "02-001"\nstage: "02"\nstatus: approved\nreviewers: [reviewer]\nallowed_paths: ["src/**"]\nexpected_commit: "feat(core): next task"\napproved_contract_sha256: null\n---\n\n# Scope\nNext task.\n\n# Completion summary\n`;
    await fs.writeFile(path.join(dir, 'docs', 'stages', 'tasks', '02-001.md'), task, 'utf8');
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'task', stageId: '02', taskId: '02-001', taskDocPath: 'docs/stages/tasks/02-001.md', next: 'approved', reason: 'owner approved' });
    state = JSON.parse(read(statePath));
    assert(state.current_task.id === '02-001', 'new task must replace completed task');
  } finally { cleanupRepo(dir); }
}

async function testQualityGateRestrictions() {
  const dir = tempRepo('gate-test-');
  const external = await fs.mkdtemp(path.join(os.tmpdir(), 'outside-gate-'));
  try {
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), { schema_version: 1, gates: [{ name: 'skip', scopes: ['task'], enabled: false, command: 'pnpm', args: ['lint'] }] });
    const mod = await importTool('./../project/.omp/tools/quality_gate.ts');
    let result = await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    assert(result.details.report.verdict === 'SKIP', 'disabled gate should yield SKIP, not PASS');

    for (const gate of [
      { name: 'escape', scopes: ['task'], enabled: true, cwd: '../..', command: 'pytest', args: [] },
      { name: 'npx', scopes: ['task'], enabled: true, command: 'npx', args: ['foo'] },
      { name: 'python-inline', scopes: ['task'], enabled: true, command: 'python3', args: ['-c', 'print(1)'] },
    ]) {
      await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), { schema_version: 1, gates: [gate] });
      let failed = false;
      try { await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' }); } catch { failed = true; }
      assert(failed, `${gate.name} must be blocked`);
    }

    symlinkSync(external, path.join(dir, 'outside-link'));
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), { schema_version: 1, gates: [{ name: 'symlink', scopes: ['task'], enabled: true, cwd: 'outside-link', command: 'pytest', args: [] }] });
    let failed = false;
    try { await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' }); } catch { failed = true; }
    assert(failed, 'symlink cwd escape must fail');
  } finally {
    cleanupRepo(dir);
    await fs.rm(external, { recursive: true, force: true });
  }
}

async function testReviewReport() {
  const dir = tempRepo('review-report-test-');
  try {
    await seedFactoryRepo(dir);
    await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 9;\n', 'utf8');
    const mod = await importTool('./../project/.omp/tools/review_report.ts');
    const result = await mod.executeReviewReport(fakePi(dir), { taskId: '01-001', reviewerRole: 'reviewer', verdict: 'approve', findings: [] });
    const report = JSON.parse(read(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json')));
    assert(report.diff_hash && report.reviewer_role === 'reviewer', 'review report must bind role and diff');
    assert(String(result.content[0].text).includes('recorded'), 'review report result should confirm storage');
  } finally { cleanupRepo(dir); }
}

async function testTaskCommitBlocksAndSuccess() {
  const mod = await importTool('./../project/.omp/tools/task_commit.ts');
  for (const scenario of ['protected', 'missing-review', 'unexpected', 'stale', 'changed-contract', 'wrong-message']) {
    const dir = await prepareCommitRepo();
    try {
      if (scenario === 'protected') git(dir, ['checkout', '-q', 'main']);
      if (scenario === 'missing-review') await fs.rm(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'));
      if (scenario === 'unexpected') await fs.writeFile(path.join(dir, 'secret.txt'), 'nope\n', 'utf8');
      if (scenario === 'stale') await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 3;\n', 'utf8');
      if (scenario === 'changed-contract') {
        const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
        await fs.writeFile(taskPath, read(taskPath).replace('# Scope', '# Scope changed'), 'utf8');
      }
      const message = scenario === 'wrong-message' ? 'fix(core): wrong message' : 'feat(core): complete task 01-001';
      let failed = false;
      try { await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message }); } catch { failed = true; }
      assert(failed, `${scenario} must block task_commit`);
      const state = JSON.parse(read(path.join(dir, 'docs', 'PROJECT_STATE.json')));
      assert(state.current_task.status === 'ready_to_commit', 'failed commit must not mutate task state');
    } finally { cleanupRepo(dir); }
  }

  const dir = await prepareCommitRepo();
  try {
    const before = Number(git(dir, ['rev-list', '--count', 'HEAD']));
    const result = await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
    assert(Number(git(dir, ['rev-list', '--count', 'HEAD'])) === before + 1, 'successful task commit must create one commit');
    assert(git(dir, ['status', '--porcelain']) === '', 'tree must be clean after task commit');
    assert(String(result.content[0].text).includes('Committed 01-001'), 'result should mention task');

    const nextTask = `---\nid: "01-002"\nstage: "01"\nstatus: approved\nreviewers: [reviewer]\nallowed_paths: ["src/**"]\nexpected_commit: "feat(core): complete task 01-002"\napproved_contract_sha256: null\n---\n\n# Scope\nSecond task.\n\n# Completion summary\n`;
    await fs.writeFile(path.join(dir, 'docs', 'stages', 'tasks', '01-002.md'), nextTask, 'utf8');
    const stateTool = await importTool('./../project/.omp/tools/project_state.ts');
    await stateTool.executeProjectState(fakePi(dir), { action: 'transition', actor: 'Main', scope: 'task', stageId: '01', taskId: '01-002', taskDocPath: 'docs/stages/tasks/01-002.md', next: 'approved', reason: 'next approved task' });
    const state = JSON.parse(read(path.join(dir, 'docs', 'PROJECT_STATE.json')));
    assert(state.current_task.id === '01-002', 'second task must become current after first commit');
  } finally { cleanupRepo(dir); }
}

async function testMissionCommit() {
  const dir = tempRepo('mission-test-');
  try {
    await seedFactoryRepo(dir);
    const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
    const state = JSON.parse(read(statePath));
    state.current_stage.status = 'planned';
    state.current_task = null;
    await writeJson(statePath, state);
    await fs.writeFile(path.join(dir, 'docs', 'plan.md'), '# Plan\n', 'utf8');
    const runtime = await importTool('./../project/.omp/tools/lib/runtime.ts');
    const branch = git(dir, ['branch', '--show-current']);
    const head = git(dir, ['rev-parse', 'HEAD']);
    const hash = await runtime.diffHash(fakePi(dir));
    await writeJson(path.join(dir, '.project-factory', 'reports', 'quality-mission-plan_stage-latest.json'), { schema_version: 1, scope: 'mission', id: 'plan_stage', verdict: 'PASS', branch, head, diff_hash: hash, gates: [{ name: 'docs', status: 'PASS' }] });
    await writeJson(path.join(dir, '.project-factory', 'reviews', 'mission-plan_stage--documentation-reviewer.json'), { schema_version: 1, task_id: 'mission-plan_stage', reviewer_role: 'documentation-reviewer', verdict: 'approve', branch, head, diff_hash: hash, findings: [] });
    const mod = await importTool('./../project/.omp/tools/mission_commit.ts');
    const result = await mod.executeMissionCommit(fakePi(dir), { mission: 'plan_stage', message: 'docs(stage): record approved plan' });
    assert(String(result.content[0].text).includes('Mission committed plan_stage'), 'mission commit should succeed with fresh evidence');

    await fs.writeFile(path.join(dir, 'src', 'bad.ts'), 'export const bad = true;\n', 'utf8');
    let failed = false;
    try { await mod.executeMissionCommit(fakePi(dir), { mission: 'plan_stage', message: 'docs(stage): hide code change' }); } catch { failed = true; }
    assert(failed, 'mission_commit must block application code');
  } finally { cleanupRepo(dir); }
}

async function testGitInspect() {
  const dir = tempRepo('inspect-test-');
  try {
    await seedFactoryRepo(dir);
    const mod = await importTool('./../project/.omp/tools/git_inspect.ts');
    const branch = await mod.executeGitInspect(fakePi(dir), { action: 'current_branch' });
    assert(String(branch.content[0].text).startsWith('stage/'), 'git_inspect should report current branch');
  } finally { cleanupRepo(dir); }
}

async function testInstallPreservesOwnerFiles() {
  const dir = tempRepo('install-test-');
  const root = path.resolve('.');
  try {
    await fs.writeFile(path.join(dir, 'PROJECT_BRIEF.md'), 'OWNER BRIEF\n', 'utf8');
    const customState = { schema_version: 2, project: { phase: 'implementation', architecture_version: 'owner' }, current_stage: null, current_task: null, blocked_by: null, history: [] };
    await writeJson(path.join(dir, 'docs', 'PROJECT_STATE.json'), customState);
    execFileSync('bash', ['install.sh', dir], { cwd: root, stdio: 'pipe' });
    assert(!existsSync(path.join(dir, '.omp')), 'dry-run must not create files');
    execFileSync('bash', ['install.sh', '--apply', dir], { cwd: root, stdio: 'pipe' });
    assert(read(path.join(dir, 'PROJECT_BRIEF.md')) === 'OWNER BRIEF\n', 'installer must preserve owner brief');
    assert(JSON.parse(read(path.join(dir, 'docs', 'PROJECT_STATE.json'))).project.architecture_version === 'owner', 'installer must preserve project state');
    assert(existsSync(path.join(dir, '.project-factory', 'install-ledger.json')), 'installer must create ledger');
  } finally { cleanupRepo(dir); }
}

await testStateTransitionsAndSequentialWork();
await testQualityGateRestrictions();
await testReviewReport();
await testTaskCommitBlocksAndSuccess();
await testMissionCommit();
await testGitInspect();
await testInstallPreservesOwnerFiles();
console.log('[tests] PASS');
