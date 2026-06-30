import { execFileSync } from 'node:child_process';
const oldPid = process.argv[2] || '273611';
const deadline = Date.now() + 390_000;
function statusText() {
  return execFileSync('openclaw', ['gateway', 'status'], {
    cwd: '/home/stickai/.openclaw/workspace',
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 120000
  });
}
function extractPid(text) {
  const match = text.match(/Runtime: running \(pid (\d+)/);
  return match?.[1] || null;
}
while (Date.now() < deadline) {
  const text = statusText();
  const pid = extractPid(text);
  if (pid && pid !== oldPid) {
    console.log(`PID_CHANGED ${oldPid} ${pid}`);
    console.log(text);
    process.exit(0);
  }
  await new Promise((resolve) => setTimeout(resolve, 15_000));
}
console.log('PID_UNCHANGED_AFTER_WAIT');
console.log(statusText());
process.exit(1);
