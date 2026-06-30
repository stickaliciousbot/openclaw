import { execFileSync } from 'node:child_process';
const raw = execFileSync('openclaw', ['tasks', 'list', '--runtime', 'cli', '--status', 'running', '--json'], {
  cwd: '/home/stickai/.openclaw/workspace',
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
  timeout: 120000
});
const data = JSON.parse(raw);
console.log(JSON.stringify({
  count: data.count,
  tasks: (data.tasks || []).map((task) => ({
    taskId: task.taskId,
    sourceId: task.sourceId,
    runId: task.runId,
    createdAt: task.createdAt,
    status: task.status,
    prefix: String(task.task || '').slice(0, 160)
  }))
}, null, 2));
