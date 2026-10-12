import json

def iter_json_records(path, chunk_size=1024*1024):
    """
    Incrementally read either:
      A) JSON Lines / NDJSON
      B) one large JSON array

    The function yields one Python dict at a time.
    It never intentionally loads the entire dataset into memory.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        # Find the first non-whitespace character.
        first = ""
        while True:
            c = f.read(1)
            if not c:
                return
            if not c.isspace():
                first = c
                break

        if first != "[":
            # NDJSON: first character belongs to the first line.
            line = first + f.readline()
            if line.strip():
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield obj
                except json.JSONDecodeError:
                    pass

            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield obj
                except json.JSONDecodeError:
                    continue
            return

        # Incremental parser for a JSON array.
        decoder = json.JSONDecoder()
        buffer = ""
        eof = False

        while True:
            if not eof and len(buffer) < chunk_size:
                chunk = f.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True

            pos = 0

            # Whitespace / commas / closing bracket.
            while pos < len(buffer) and buffer[pos].isspace():
                pos += 1

            if pos < len(buffer) and buffer[pos] == ",":
                pos += 1
                while pos < len(buffer) and buffer[pos].isspace():
                    pos += 1

            if pos < len(buffer) and buffer[pos] == "]":
                return

            if pos >= len(buffer):
                if eof:
                    return
                buffer = buffer[pos:]
                continue

            try:
                obj, end = decoder.raw_decode(buffer, pos)
            except json.JSONDecodeError:
                if eof:
                    return
                buffer = buffer[pos:]
                chunk = f.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
                continue

            buffer = buffer[end:]

            if isinstance(obj, dict):
                yield obj
