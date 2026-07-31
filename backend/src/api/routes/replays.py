import json
import os
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from src.analytics.features.scoreboard import flatten_player_stats
from src.db.database import get_db
from src.db.services import save_match_to_db

router = APIRouter(prefix="/api/replays", tags=["Replays"])


def resolve_upload_dir() -> Path:
    configured_dir = os.getenv("REPLAY_UPLOAD_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()

    backend_root = Path(__file__).resolve().parents[3]
    return (backend_root / "data" / "raw").resolve()


def resolve_rrrocket_path() -> str:
    rrrocket_path = shutil.which("rrrocket")
    if rrrocket_path:
        return rrrocket_path

    local_binary = Path("/usr/local/bin/rrrocket")
    if local_binary.exists():
        return str(local_binary)

    raise FileNotFoundError(
        "rrrocket is not installed or not on PATH. Install it or set REPLAY_UPLOAD_DIR."
    )


@router.post("/upload")
async def upload_replay(file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_dir = resolve_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename or "upload.replay").name
    replay_path = upload_dir / safe_filename

    try:
        replay_bytes = await file.read()
        replay_path.write_bytes(replay_bytes)

        rrrocket_path = resolve_rrrocket_path()
        result = subprocess.run(
            [rrrocket_path, "-n", "-i", str(replay_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error_output = (result.stderr or result.stdout or "Unknown rrrocket error").strip()
            raise subprocess.CalledProcessError(
                result.returncode,
                [rrrocket_path, "-n", "-i", str(replay_path)],
                output=result.stdout,
                stderr=error_output,
            )

        raw_json = json.loads(result.stdout or "{}")

        properties = raw_json.get("properties", {})
        match_guid = properties.get("MatchGUID", safe_filename)
        map_name = properties.get("MapName", "Unknown Map")
        raw_player_stats = properties.get("PlayerStats", [])

        flattened_stats = flatten_player_stats(raw_player_stats, {})

        match_record = save_match_to_db(
            db=db,
            match_guid=match_guid,
            map_name=map_name,
            flattened_stats=flattened_stats,
        )

        return {
            "status": "success",
            "message": "Replay parsed and saved to DB!",
            "match_guid": match_record.match_guid,
            "players_saved": len(match_record.players),
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"rrrocket failed: {e.stderr or e.output or str(e)}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")
