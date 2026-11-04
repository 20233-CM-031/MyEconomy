"""Private local evidence store. Production should inject an encrypted object-store adapter."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID


class DocumentStorageError(OSError):
    """Private evidence storage could not complete an operation."""


class LocalPrivateDocumentStore:
    """Filesystem adapter using generated keys, restrictive permissions and atomic writes.

    Original filenames never become storage paths. This adapter is suitable for local/demo
    deployments on a trusted host; production requires encrypted object storage, KMS-managed
    keys, malware scanning, backup/retention controls and deployment-specific access policy.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = (
            root or Path(os.getenv("AWNNORA_DOCUMENT_ROOT", ".data/private_documents"))
        ).resolve()

    def _owner_dir(self, owner_id: UUID) -> Path:
        directory = self.root / str(owner_id)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            directory.chmod(0o700)
        except OSError:
            pass
        return directory

    def put(self, *, owner_id: UUID, document_id: UUID, content: bytes) -> None:
        directory = self._owner_dir(owner_id)
        destination = directory / f"{document_id}.blob"
        temporary = directory / f".{document_id}.tmp"
        try:
            with temporary.open("xb") as handle:
                try:
                    os.chmod(temporary, 0o600)
                except OSError:
                    pass
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
            try:
                destination.chmod(0o600)
            except OSError:
                pass
        except FileExistsError:
            raise DocumentStorageError("Storage key already exists.") from None
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise DocumentStorageError("Evidence file could not be stored.") from exc

    def get(self, *, owner_id: UUID, document_id: UUID) -> bytes:
        path = self.root / str(owner_id) / f"{document_id}.blob"
        try:
            return path.read_bytes()
        except OSError as exc:
            raise DocumentStorageError("Evidence file is unavailable.") from exc

    def delete(self, *, owner_id: UUID, document_id: UUID) -> None:
        path = self.root / str(owner_id) / f"{document_id}.blob"
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise DocumentStorageError("Evidence file could not be removed.") from exc
