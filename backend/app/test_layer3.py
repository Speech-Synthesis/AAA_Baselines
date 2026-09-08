"""
Standalone unit test suite for Layer 3 Adaptive module.
Tests:
1. Challenge & HMAC token generation (phrase generation, 90s TTL)
2. Token verification & single-use enforcement
3. Token expiration check
4. Voiceprint EMA update calculation accuracy (0.8 * Old + 0.2 * Current)
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Ensure backend/app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.layer3_adaptive import (
    generate_challenge,
    verify_token,
    get_token_user_id,
    update_voiceprint,
    _token_store
)


def test_challenge_generation():
    user_id = "test-uuid-1234-5678"
    ch = generate_challenge(user_id)
    
    assert "phrase" in ch, "Challenge response must contain 'phrase'"
    assert "token" in ch, "Challenge response must contain 'token'"
    assert "expires_at" in ch, "Challenge response must contain 'expires_at'"
    assert isinstance(ch["phrase"], str) and len(ch["phrase"]) > 0
    assert isinstance(ch["token"], str) and "." in ch["token"]
    
    # Verify TTL is ~90 seconds
    ttl_seconds = (ch["expires_at"] - datetime.utcnow()).total_seconds()
    assert 85 <= ttl_seconds <= 92, f"TTL should be 90 seconds, got {ttl_seconds}"
    
    print("[PASS] test_challenge_generation passed")


def test_token_verification_and_single_use():
    user_id = "test-uuid-9999"
    ch = generate_challenge(user_id)
    token = ch["token"]
    
    # Get associated user id
    assert get_token_user_id(token) == user_id, "get_token_user_id failed"
    
    # First verification should succeed
    v1 = verify_token(token)
    assert v1 is True, "First verify_token should return True"
    
    # Second verification with same token should fail (single-use)
    v2 = verify_token(token)
    assert v2 is False, "Second verify_token must return False (single-use enforcement)"
    
    # Fake token should fail
    v3 = verify_token("fake.token.signature")
    assert v3 is False, "Fake token must return False"
    
    print("[PASS] test_token_verification_and_single_use passed")


def test_token_expiration():
    user_id = "test-uuid-expired"
    ch = generate_challenge(user_id)
    token = ch["token"]
    
    # Manually backdate expiration to simulate TTL timeout
    _token_store[token]["expires_at"] = datetime.utcnow() - timedelta(seconds=1)
    
    res = verify_token(token)
    assert res is False, "Expired token must be rejected"
    
    print("[PASS] test_token_expiration passed")


def test_update_voiceprint_ema():
    # 192-dim vectors
    old_emb = [1.0] * 192
    new_emb = [2.0] * 192
    
    # Formula: 0.8 * 1.0 + 0.2 * 2.0 = 0.8 + 0.4 = 1.2
    updated = update_voiceprint(old_emb, new_emb, alpha=0.2)
    
    assert len(updated) == 192, "Vector dimension must remain 192"
    for val in updated:
        assert abs(val - 1.2) < 1e-6, f"Expected 1.2, got {val}"
        
    # Test custom alpha (e.g. 0.5)
    updated_half = update_voiceprint([0.0]*192, [10.0]*192, alpha=0.5)
    for val in updated_half:
        assert abs(val - 5.0) < 1e-6, f"Expected 5.0, got {val}"
        
    print("[PASS] test_update_voiceprint_ema passed")


if __name__ == "__main__":
    print("Running Layer 3 standalone unit tests...")
    test_challenge_generation()
    test_token_verification_and_single_use()
    test_token_expiration()
    test_update_voiceprint_ema()
    print("\nALL LAYER 3 TESTS PASSED PERFECTLY!")
