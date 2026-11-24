"""Register private generated files against exact venture inputs."""

from hashlib import file_digest
from pathlib import Path

from .schema import relative_document, require
from .workspace import plain


def register(workspace, relative, *, name, document_type, links, expected=None):
    relative = relative_document(relative)
    path = workspace.root
    for part in Path(relative).parts:
        path /= part
        require(plain(path), "Linked document path refused")
    require(path.is_file() and not relative.startswith((".seed/", "backups/")),
            "Document must be a regular workspace output")
    require(links, "A generated document requires pinned inputs")
    with path.open("rb") as stream:
        checksum = file_digest(stream, "sha256").hexdigest()
    return workspace.put("document", relative, {"name": name, "document_type": document_type,
                         "document_ref": relative, "sha256": checksum}, expected=expected,
                         provenance="calculated", classification="restricted", links=links)
