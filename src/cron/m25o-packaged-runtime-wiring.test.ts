import { describe, expect, it } from "vitest";
import {
  M25O_PACKAGED_RUNTIME_WIRING_REPAIR_TERMINAL,
  runM25OPackagedRuntimeNoSendSmoke,
  runM25NTelegramCanaryHarness,
} from "./m25o-packaged-runtime-wiring.js";

describe("M25O-A-R packaged runtime wiring", () => {
  it("exports the M25N harness without executing it at import time", () => {
    expect(typeof runM25NTelegramCanaryHarness).toBe("function");
  });

  it("runs the delivery-contract no-send smoke without provider sends", async () => {
    const receipt = await runM25OPackagedRuntimeNoSendSmoke();
    expect(receipt.terminal).toBe(M25O_PACKAGED_RUNTIME_WIRING_REPAIR_TERMINAL);
    expect(receipt.chainTerminal).toBe("PASS_SANITIZED_PAYLOAD_TARGET_ARTIFACT_NO_SEND");
    expect(receipt.providerSendAttempted).toBe(false);
    expect(receipt.providerInvocationCount).toBe(0);
    expect(receipt.telegramDeliveredMessageCount).toBe(0);
    expect(receipt.adapterTerminal).toBe("TARGET_BINDING_INVALID_NO_DELIVERY");
    expect(receipt.errors).toEqual([]);
    expect(receipt.importedRuntimeModules).toEqual([
      "boundary-decision-envelope",
      "runtime-delivery-classification",
      "sanitized-payload-target-artifact",
      "telegram-delivery-adapter-canary",
      "m25n-telegram-canary-harness",
    ]);
    expect(receipt.payloadSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(receipt.targetReceiptSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(receipt.resultSha256).toMatch(/^[a-f0-9]{64}$/);
    expect(receipt.chainSha256).toMatch(/^[a-f0-9]{64}$/);
  });
});
