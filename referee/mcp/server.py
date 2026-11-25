from __future__ import annotations

"""Beihang Referee as an MCP server: Referee directs, YOUR AI reviews.

Connect this server to any MCP-capable assistant (Claude, ChatGPT connectors,
Cursor, local clients). The assistant does the reading and writing with its own
model, so Referee needs no API key. Referee supplies the workflow, the rules,
and deterministic checks the assistant cannot fake: exact-quote verification,
numerical and reference checks, passage retrieval, a concern admission gate, a
graded editorial decision, and a frozen ledger for revision rounds.

Start with `get_playbook`, then `start_review`.
"""

from typing import Any


def build_server():
    try:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:  # mcp 2.x renamed FastMCP to MCPServer
            from mcp.server.mcpserver import MCPServer as FastMCP
        except ImportError as exc:
            raise RuntimeError("MCP support requires the optional `mcp` package: pip install mcp") from exc
    from .. import direction as D
    from ..ingestion import PackageInspector
    from ..comparison import revision_diff, audit_rebuttal_structure
    from ..documents import DocumentLoader
    from ..modes import ReviewModeRegistry

    mcp = FastMCP("Beihang Referee")

    @mcp.tool()
    def get_playbook(stage: str | None = None) -> dict:
        """START HERE. Returns the review workflow (what you, the AI, do at each step), plus the rules for voice, stopping, decision calibration and the path-to-a-stronger-paper. Optional stage: voice, stopping, decision, elevation, evidence."""
        return D.playbook(stage)

    @mcp.tool()
    def start_review(path: str | None = None, text: str | None = None) -> dict:
        """Load a manuscript (file path: pdf, docx, md, txt, tex) or pasted text. Returns a manuscript_id used by the other tools, the opening text, and the playbook."""
        return D.start_review(path, text)

    @mcp.tool()
    def find_passages(manuscript_id: str, query: str, k: int = 5) -> dict:
        """Retrieve the passages of the manuscript most relevant to a query (BM25). Use it to locate evidence before raising a concern."""
        return D.find_passages(D.Session.load(manuscript_id), query, k)

    @mcp.tool()
    def verify_quote(manuscript_id: str, quote: str) -> dict:
        """Check that a quote really appears in the manuscript (whitespace/case tolerant). Every concern anchor must pass this. Returns verified or not_found."""
        return D.verify_quote(D.Session.load(manuscript_id), quote)

    @mcp.tool()
    def check_numbers(manuscript_id: str) -> dict:
        """Offline recomputation: reported test statistics vs p-values (t, F, chi2, r, z), GRIM on means, counts vs percentages, citation numbering, duplicate DOIs. Objective facts to cite."""
        return D.check_numbers(D.Session.load(manuscript_id))

    @mcp.tool()
    def check_references(manuscript_id: str) -> dict:
        """Verify cited DOIs against Crossref (existence, retraction notices, title match) and list possible uncited prior art from Europe PMC. Needs internet, no key."""
        return D.check_references(D.Session.load(manuscript_id))

    @mcp.tool()
    def check_figures(pdf_path: str) -> dict:
        """Find duplicated or re-used images inside a PDF's figures (perceptual hashing, flips, rotations, quadrants). Findings mean 'a human should compare these two images', never proof of misconduct. Needs pymupdf and pillow."""
        from ..verification.figures import check_figures as _cf
        return _cf(pdf_path)

    @mcp.tool()
    def submit_concerns(manuscript_id: str, claims: list[dict[str, Any]], concerns: list[dict[str, Any]]) -> dict:
        """The admission gate and decision. claims: [{claim_id, text, centrality: central|supporting}]. concerns: [{title, claim_ids, anchors:[exact quotes], failure_mechanism, scientific_consequence, consequence_level: invalidates|changes_interpretation|weakens|minor, minimum_resolution, closure_criterion, confidence 0-1, steelman, steelman_survival}]. Returns admitted vs downgraded concerns (with reasons) and the editorial recommendation you must use. Freezes the ledger for revision rounds."""
        return D.submit_concerns(D.Session.load(manuscript_id), claims, concerns)

    @mcp.tool()
    def revision_round(new_manuscript_id: str, prior_manuscript_id: str, statuses: dict[str, dict[str, Any]],
                       new_concerns: list[dict[str, Any]] | None = None) -> dict:
        """Judge a revised manuscript against the FROZEN ledger of the first review. statuses: {concern_id: {status: OPEN|PARTIAL|VERIFIED_CLOSED|WORSENED, evidence_quote: exact quote from the revision (required to close), note}}. new_concerns need origin introduced_by_revision, missed_factual_error, or field_development (then also external_source: DOI/URL), with anchors in the revised text; anything else is rejected as moving the goalposts."""
        return D.revision_round(D.Session.load(new_manuscript_id), prior_manuscript_id, statuses, new_concerns)

    @mcp.tool()
    def inspect_package(paths: list[str]) -> dict:
        """Inspect manuscript/reproducibility package structure without running a model."""
        return PackageInspector().inspect(paths).to_dict()

    @mcp.tool()
    def compare_revision(old_path: str, new_path: str) -> dict:
        """Compare two manuscript versions structurally."""
        loader = DocumentLoader()
        return revision_diff(loader.load(old_path).text, loader.load(new_path).text)

    @mcp.tool()
    def audit_rebuttal(response_path: str) -> dict:
        """Audit reviewer-response traceability signals."""
        return audit_rebuttal_structure(DocumentLoader().load(response_path).text)

    @mcp.tool()
    def list_review_modes() -> list[str]:
        """List supported review purposes."""
        return ReviewModeRegistry().names()

    return mcp


def main():
    build_server().run()


if __name__ == "__main__":
    main()
