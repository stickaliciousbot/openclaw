# Failed attempts retained

1. Initial validator proof build swapped epoch/fence tuple positions and used a null T00 predecessor state. Validator correctly held; generation was corrected at source and baseline passed.
2. First mutation sweep exposed an uninitialized `txt` variable on mutated design paths. Validator source was corrected without weakening the gate; all suites then passed.
3. First privacy invocation used an incompatible CLI signature. The exact frozen scanner usage was inspected and rerun with its required root/output/scanner/detector hashes; bounded scan passed.
