from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dtb_compiler import CompileContext, compile_douglas_dtb_definition


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile Douglas DTB definition parts locally")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--lakehouse-id", required=True)
    parser.add_argument("--dtb-name", default="DouglasBagmakerDTB")
    parser.add_argument(
        "--source-schema",
        default="null",
        help="Lakehouse schema for source tables. Use 'null' for root Tables/<table> paths; app-loaded Douglas tables must omit SourceSchema.",
    )
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    ctx = CompileContext(
        workspace_id=args.workspace_id,
        lakehouse_id=args.lakehouse_id,
        dtb_name=args.dtb_name,
        source_schema=args.source_schema if args.source_schema != "null" else None,
    )
    result = compile_douglas_dtb_definition(ctx, args.out)
    print(json.dumps({"status": "ok", "out": str(args.out), "partCount": len(result["parts"])}, indent=2))


if __name__ == "__main__":
    main()
