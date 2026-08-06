import { mkdtempSync, rmSync, writeFileSync, mkdirSync, existsSync, readFileSync } from "node:fs";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

export function tempRepo(prefix = 'factory-test-') {
  const dir = mkdtempSync(path.join(os.tmpdir(), prefix));
  execFileSync('git', ['init', '-q', dir]);
  execFileSync('git', ['-C', dir, 'config', 'user.email', 'factory@example.com']);
  execFileSync('git', ['-C', dir, 'config', 'user.name', 'Factory Test']);
  mkdirSync(path.join(dir, 'docs', 'stages'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'reports'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'reviews'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'github-outbox'), { recursive: true });
  mkdirSync(path.join(dir, 'src'), { recursive: true });
  writeFileSync(path.join(dir, 'docs', 'stages', '01-README.md'), '# Stage 01\n', 'utf8');
  writeFileSync(path.join(dir, 'src', 'main.ts'), 'export const x = 1;\n', 'utf8');
  execFileSync('git', ['-C', dir, 'add', '.']);
  execFileSync('git', ['-C', dir, 'commit', '-q', '-m', 'chore: init repo']);
  execFileSync('git', ['-C', dir, 'branch', '-m', 'main']);
  return dir;
}

export function cleanupRepo(dir) {
  rmSync(dir, { recursive: true, force: true });
}

export function git(dir, args) {
  return execFileSync('git', ['-C', dir, ...args], { encoding: 'utf8' }).trim();
}

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));

export async function importTool(relativePath) {
  return import(pathToFileURL(path.resolve(THIS_DIR, relativePath)).href);
}

export function fakePi(cwd) {
  return {
    cwd,
    async exec(command, args, options = {}) {
      try {
        const stdout = execFileSync(command, args, {
          cwd: options.cwd ?? cwd,
          encoding: 'utf8',
          timeout: options.timeout ? options.timeout * 1000 : undefined,
          stdio: ['ignore', 'pipe', 'pipe'],
        });
        return { stdout, stderr: '', code: 0, killed: false };
      } catch (error) {
        return {
          stdout: error.stdout ? String(error.stdout) : '',
          stderr: error.stderr ? String(error.stderr) : error.message,
          code: typeof error.status === 'number' ? error.status : 1,
          killed: false,
        };
      }
    },
  };
}

export async function writeJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

export async function seedFactoryRepo(dir) {
  const state = {
    schema_version: 2,
    project: { phase: 'implementation', architecture_version: 'v1' },
    current_stage: { id: '01', status: 'active', readme_path: 'docs/stages/01-README.md' },
    current_task: {
      id: '01-001',
      stage_id: '01',
      status: 'ready_to_commit',
      doc_path: 'docs/stages/tasks/01-001.md',
      expected_commit: 'feat(core): complete task 01-001',
      allowed_paths: ['src/**', 'docs/**', '.project-factory/**'],
      reviewers: ['reviewer'],
      approved_contract_sha256: null,
      started_head: null,
    },
    blocked_by: null,
    history: [],
  };
  await writeJson(path.join(dir, 'docs', 'PROJECT_STATE.json'), state);
  await fs.mkdir(path.join(dir, 'docs', 'stages', 'tasks'), { recursive: true });
  const taskDoc = `---\nid: "01-001"\nstage: "01"\nstatus: "ready_to_commit"\ntitle: "Task"\ntype: "feature"\nrisk: "medium"\nreviewers: [reviewer]\nallowed_paths: ["src/**", "docs/**", ".project-factory/**"]\nexpected_commit: "feat(core): complete task 01-001"\napproved_contract_sha256: null\nsensitive: false\ndata_change: false\nperformance_sensitive: false\ninfrastructure_change: false\n---\n\n# Scope\n\nTask body.\n\n# Completion summary\n\nPending.\n`;
  await fs.writeFile(path.join(dir, 'docs', 'stages', 'tasks', '01-001.md'), taskDoc, 'utf8');
  await fs.writeFile(path.join(dir, '.project-factory', 'quality-gates.json'), JSON.stringify({ schema_version: 1, gates: [] }, null, 2) + '\n', 'utf8');
  git(dir, ['add', '.']);
  git(dir, ['commit', '-q', '-m', 'chore: seed repo']);
  const seedHead = git(dir, ['rev-parse', 'HEAD']);
  const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
  const persistedState = JSON.parse(readFileSync(statePath, 'utf8'));
  persistedState.current_task.started_head = seedHead;
  writeFileSync(statePath, JSON.stringify(persistedState, null, 2) + '\n', 'utf8');
  git(dir, ['checkout', '-q', '-b', 'stage/01-foundation']);
}

export function assert(condition, message) {
  if (!condition) throw new Error(message);
}

export function read(file) {
  return readFileSync(file, 'utf8');
}
