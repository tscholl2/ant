def lines_in_env(environment,lines):
    """
    Given some lines of tex code and an environment (such as "enumerate" or "align")
    this returns the index of the first line that starts with "\\begin{environment}"
    and the number of lines until "\\end{environment}".

    Note: lines[start:start+length] should include both the begin and end lines.
    """
    is_start = lambda line: line.strip().startswith("\\begin{%s}" % environment)
    is_end   = lambda line: line.strip().startswith("\\end{%s}"   % environment)
    start    = next(i for i,line in enumerate(lines) if is_start(line))
    length   = next(i+1 for i,line in enumerate(lines[start:]) if is_end(line))
    return start,length

def get_blocks(tex):
    """
    Given a string of tex, returns the lines of {sagecell}
    environments grouped together by {sagecode} environments
    respecting "%link" commands.
    """
    lines = tex.splitlines()
    blocks = []
    i = 0
    while True:
        try:
            start,length = lines_in_env("sagecode",lines[i:])
            blocks.append({
                "start": i+start,
                "length": length,
            })
            i += start + length
        except StopIteration:
            break
    cells = [[]]
    for block in blocks:
        start,length = block["start"],block["length"]
        j = 0
        while True:
            try:
                cell_start,cell_length = lines_in_env("sagecell",lines[start+j:start+length])
                out_start,out_length = lines_in_env("sageout",lines[start+j:start+length])
                assert cell_start + cell_length == out_start
                if not lines[start+j+cell_start].strip().endswith("%skip"):
                    cells[-1].append({
                        "source": {"start":cell_start+j+start,"length":cell_length},
                        "output": {"start":out_start+j+start,"length":out_length},
                    })
                j += cell_length + out_length
            except StopIteration:
                break
        if not lines[start+length-1].strip().endswith("%link"):
            cells.append([])
    return [a for a in cells if len(a) > 0]


def generate_tests(tex,filename="__FILE__"):
    """
    Given a string of tex, this returns a sage file
    containing all the code with comments for line numbers.
    This can be used to test the code samples.
    """
    lines = tex.splitlines()
    output = "\n\n"
    blocks = get_blocks(tex)

    for block in blocks:
        output += "\"\"\"\n"
        for cell in block:
            source_start,source_length = cell["source"]["start"],cell["source"]["length"]
            for i in range(source_start + 1,source_start + source_length - 1):
                if lines[i].startswith("\t") or lines[i].startswith("  ") or lines[i-1].strip().endswith("\\"):
                    prefix = "....: "
                else:
                    prefix = "sage: "
                if lines[i].strip().endswith("\\"):
                    suffix = ""
                else:
                    suffix = f" # {filename}:{i+1}"
                output += prefix + lines[i].replace("\t","    ") + suffix + "\n"
            out_start,out_length = cell["output"]["start"],cell["output"]["length"]
            for i in range(out_start + 1,out_start + out_length - 1):
                output += lines[i] + "\n"
        output += "\"\"\"\n\n"
    return output

if __name__ == "__main__":
    # find files and generate tests
    import os
    tests = ""
    #for f in [f for f in os.listdir(".") if f.endswith(".tex")][3:4]:
    for f in ["ch02.tex"]:
        with open(f) as file:
            tests += f"\n\n\n{generate_tests(file.read(),file.name)}\n\n\n"
    # write tests to tmp file
    with open("/tmp/test.sage","wt") as file:
        file.write(tests)
    #run tests
    import os
    print(os.popen('sage -t /tmp/test.sage').read())
