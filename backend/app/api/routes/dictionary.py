from fastapi import APIRouter, HTTPException, Path

from app.schemas.dictionary import DictionaryEntry
from app.services.dictionary import get_dictionary_entry

router = APIRouter()


@router.get("/dictionary/{word}", response_model=DictionaryEntry)
def lookup_word(
    word: str = Path(min_length=1, max_length=50),
) -> DictionaryEntry:
    try:
        return get_dictionary_entry(word)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
