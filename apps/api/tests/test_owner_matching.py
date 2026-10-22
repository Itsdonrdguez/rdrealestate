from pipelines.owners.matching import OwnerIdentity, match_owner, normalize_owner_name


def test_owner_name_normalization_is_conservative() -> None:
    assert normalize_owner_name("ABC Properties, L.L.C.") == "ABC PROPERTIES"
    assert normalize_owner_name("ABC Property Group") == "ABC PROPERTY GROUP"


def test_exact_name_and_address_can_be_confirmed() -> None:
    owner = OwnerIdentity("ABC PROPERTIES", "10 MAIN ST BOWIE MD 20715")
    decision = match_owner(owner, owner)
    assert decision.matched is True
    assert decision.status == "confirmed"
    assert decision.confidence == 1.0


def test_name_only_match_remains_candidate() -> None:
    candidate = OwnerIdentity("ABC PROPERTIES", None)
    existing = OwnerIdentity("ABC PROPERTIES", "10 MAIN ST BOWIE MD 20715")
    decision = match_owner(candidate, existing)
    assert decision.matched is False
    assert decision.status == "candidate"
