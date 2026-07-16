"""
Render equation block as a png
"""

import subprocess
import tempfile
from pathlib import Path

import pdf2image


def get_eqn(path="docs/lpl.md") -> str:
    """Collect the first back-ticked math block from `path`"""
    lines = []
    in_eq = False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not in_eq and line == "```math":
                in_eq = True
            elif in_eq and line == "```":
                in_eq = False
                break
            elif in_eq:
                lines.append(line)
            else:
                pass

    return "\n".join(lines)


def latex_to_png(latex_str: str, out_path: str, dpi: int = 400, verbose: bool = False):
    """Render `latex_str` using pdflatex"""
    content = (
        r"""
\documentclass[preview,border=2pt]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
%s
\end{document}
"""
        % latex_str
    )

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "eq.tex"
        path.write_text(content)
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                td,
                str(path),
            ],
            capture_output=True,
        )

        if verbose:
            print(result.stdout.decode("utf-8"))
            print(result.stderr.decode("utf-8"))

        pages = pdf2image.convert_from_path(str(Path(td) / "eq.pdf"), dpi=dpi)

    pages[0].save(out_path, "PNG")


if __name__ == "__main__":
    eqn = get_eqn()
    print(eqn)
    latex_to_png(eqn, "tmp_eqn.png", verbose=False)
