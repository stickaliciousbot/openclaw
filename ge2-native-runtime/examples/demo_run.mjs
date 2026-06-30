import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildGe2Envelope } from '../src/ge2_command_router.mjs';
import { Ge2Dispatcher } from '../src/ge2_dispatcher.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..', 'state', 'demo-ledger');

const dispatcher = new Ge2Dispatcher({
  stateDir: rootDir,
  artifactDir: path.join(rootDir, 'artifacts')
});

const runEnvelopeResult = buildGe2Envelope({
  input: '/ge2 run daily-maintenance',
  origin: {
    surface: 'demo',
    channel: 'demo',
    sessionKey: 'demo-session'
  }
});

if (!runEnvelopeResult.ok) {
  console.error('Envelope error:', runEnvelopeResult.error);
  process.exit(1);
}

const accepted = await dispatcher.dispatch(runEnvelopeResult.envelope);
console.log('accepted:', JSON.stringify(accepted, null, 2));

const runId = accepted.run_id;
for (let i = 0; i < 20; i += 1) {
  const status = await dispatcher.status(runId);
  const currentStatus = status?.run?.status || 'unknown';
  console.log(`status[${i}]: ${currentStatus}`);
  if (['completed', 'failed', 'cancelled'].includes(currentStatus)) {
    console.log('final status:', JSON.stringify(status, null, 2));
    break;
  }
  await new Promise((resolve) => setTimeout(resolve, 200));
}

const artifacts = await dispatcher.artifacts(runId);
console.log('artifacts:', JSON.stringify(artifacts, null, 2));
