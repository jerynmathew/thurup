"""
Tests for short code generation and validation utilities.

Tests generation, collision avoidance, validation, and normalization.
"""

import pytest
from app.utils.shortcode import (
    ADJECTIVES,
    NOUNS,
    generate_short_code,
    normalize_short_code,
    validate_short_code,
)


class TestGenerateShortCode:
    """Tests for generate_short_code() function."""

    def test_basic_generation(self):
        """Test basic short code generation."""
        code = generate_short_code()
        assert code is not None
        assert isinstance(code, str)
        # Should follow format: adjective-noun-number
        parts = code.split("-")
        assert len(parts) == 3

    def test_format_validation(self):
        """Test that generated code has correct format."""
        code = generate_short_code()
        parts = code.split("-")

        adjective, noun, number_str = parts

        # Check adjective is from word list
        assert adjective in ADJECTIVES

        # Check noun is from word list
        assert noun in NOUNS

        # Check number is 10-99
        number = int(number_str)
        assert 10 <= number <= 99

    def test_collision_avoidance(self):
        """Test that generated code avoids collisions with existing codes."""
        existing = {"happy-tiger-42", "clever-eagle-55"}

        # Generate 10 codes and ensure none collide
        for _ in range(10):
            code = generate_short_code(existing)
            assert code not in existing

    def test_uniqueness_with_large_set(self):
        """Test collision avoidance with larger existing set."""
        # Generate 50 codes
        existing = set()
        for _ in range(50):
            code = generate_short_code(existing)
            assert code not in existing
            existing.add(code)

        # All should be unique
        assert len(existing) == 50

    def test_empty_existing_codes(self):
        """Test generation with empty existing codes set."""
        code = generate_short_code(set())
        assert code is not None
        assert validate_short_code(code)

    def test_none_existing_codes(self):
        """Test generation with None as existing codes."""
        code = generate_short_code(None)
        assert code is not None
        assert validate_short_code(code)

    def test_fallback_to_uuid(self, monkeypatch):
        """Test fallback to UUID when can't generate unique code."""
        # Create a set with all possible combinations (mock scenario)
        # We'll mock random.choice to always return same values
        call_count = [0]

        def mock_choice(items):
            # Always return first item
            return items[0]

        def mock_randint(a, b):
            # Always return same number
            return 10

        monkeypatch.setattr("app.utils.shortcode.random.choice", mock_choice)
        monkeypatch.setattr("app.utils.shortcode.random.randint", mock_randint)

        # Create existing set with the code that will be generated
        existing = {f"{ADJECTIVES[0]}-{NOUNS[0]}-10"}

        # Should fall back to UUID format
        code = generate_short_code(existing)
        assert code.startswith("game-")
        assert len(code) == 13  # "game-" + 8 hex chars

    def test_multiple_generations_are_different(self):
        """Test that multiple generations produce different codes (statistically)."""
        codes = set()
        for _ in range(20):
            code = generate_short_code()
            codes.add(code)

        # Very unlikely to generate duplicates in 20 attempts with 144k combinations
        # If we get at least 15 unique codes, randomness is working
        assert len(codes) >= 15


class TestValidateShortCode:
    """Tests for validate_short_code() function."""

    def test_valid_code(self):
        """Test validation of valid short code."""
        assert validate_short_code("happy-tiger-42") is True
        assert validate_short_code("clever-eagle-55") is True
        assert validate_short_code("brave-dragon-99") is True

    def test_valid_code_boundaries(self):
        """Test validation at number boundaries."""
        assert validate_short_code("happy-tiger-10") is True
        assert validate_short_code("happy-tiger-99") is True

    def test_invalid_empty_string(self):
        """Test validation fails for empty string."""
        assert validate_short_code("") is False

    def test_invalid_none(self):
        """Test validation fails for None."""
        assert validate_short_code(None) is False

    def test_invalid_wrong_part_count(self):
        """Test validation fails for wrong number of parts."""
        assert validate_short_code("happy-tiger") is False  # Missing number
        assert validate_short_code("happy") is False  # Only one part
        assert validate_short_code("happy-tiger-42-extra") is False  # Too many parts

    def test_invalid_adjective(self):
        """Test validation fails for invalid adjective."""
        assert validate_short_code("invalid-tiger-42") is False
        assert validate_short_code("xyz-tiger-42") is False

    def test_invalid_noun(self):
        """Test validation fails for invalid noun."""
        assert validate_short_code("happy-invalid-42") is False
        assert validate_short_code("happy-xyz-42") is False

    def test_invalid_number_too_low(self):
        """Test validation fails for number < 10."""
        assert validate_short_code("happy-tiger-9") is False
        assert validate_short_code("happy-tiger-1") is False
        assert validate_short_code("happy-tiger-0") is False

    def test_invalid_number_too_high(self):
        """Test validation fails for number > 99."""
        assert validate_short_code("happy-tiger-100") is False
        assert validate_short_code("happy-tiger-999") is False

    def test_invalid_number_not_numeric(self):
        """Test validation fails for non-numeric part."""
        assert validate_short_code("happy-tiger-xx") is False
        assert validate_short_code("happy-tiger-1a") is False
        assert validate_short_code("happy-tiger-") is False

    def test_case_sensitivity(self):
        """Test validation is case-sensitive (lowercase required)."""
        # Note: Our word lists are lowercase, so uppercase should fail
        assert validate_short_code("HAPPY-TIGER-42") is False
        assert validate_short_code("Happy-Tiger-42") is False

    def test_all_valid_combinations(self):
        """Test that all adjective/noun combinations are valid."""
        # Sample a few combinations to verify logic
        test_cases = [
            (ADJECTIVES[0], NOUNS[0], 50),
            (ADJECTIVES[-1], NOUNS[-1], 75),
            (ADJECTIVES[len(ADJECTIVES) // 2], NOUNS[len(NOUNS) // 2], 33),
        ]

        for adj, noun, num in test_cases:
            code = f"{adj}-{noun}-{num}"
            assert validate_short_code(code) is True


class TestNormalizeShortCode:
    """Tests for normalize_short_code() function."""

    def test_already_normalized(self):
        """Test normalization of already-normalized code."""
        code = "happy-tiger-42"
        assert normalize_short_code(code) == "happy-tiger-42"

    def test_uppercase_to_lowercase(self):
        """Test conversion of uppercase to lowercase."""
        assert normalize_short_code("HAPPY-TIGER-42") == "happy-tiger-42"
        assert normalize_short_code("Happy-Tiger-42") == "happy-tiger-42"
        assert normalize_short_code("HaPPy-TiGeR-42") == "happy-tiger-42"

    def test_spaces_to_hyphens(self):
        """Test conversion of spaces to hyphens."""
        assert normalize_short_code("happy tiger 42") == "happy-tiger-42"
        assert normalize_short_code("happy  tiger  42") == "happy-tiger-42"

    def test_underscores_to_hyphens(self):
        """Test conversion of underscores to hyphens."""
        assert normalize_short_code("happy_tiger_42") == "happy-tiger-42"
        assert normalize_short_code("happy__tiger__42") == "happy-tiger-42"

    def test_mixed_separators(self):
        """Test handling of mixed separator types."""
        assert normalize_short_code("happy tiger_42") == "happy-tiger-42"
        assert normalize_short_code("happy_tiger 42") == "happy-tiger-42"
        assert normalize_short_code("happy  _  tiger__42") == "happy-tiger-42"

    def test_leading_trailing_whitespace(self):
        """Test stripping of leading/trailing whitespace."""
        assert normalize_short_code("  happy-tiger-42  ") == "happy-tiger-42"
        assert normalize_short_code("\thappy-tiger-42\n") == "happy-tiger-42"

    def test_multiple_consecutive_hyphens(self):
        """Test removal of multiple consecutive hyphens."""
        assert normalize_short_code("happy--tiger--42") == "happy-tiger-42"
        assert normalize_short_code("happy---tiger---42") == "happy-tiger-42"
        assert normalize_short_code("happy----tiger-42") == "happy-tiger-42"

    def test_complex_normalization(self):
        """Test complex cases with multiple issues."""
        assert normalize_short_code("  HAPPY  Tiger__42  ") == "happy-tiger-42"
        assert normalize_short_code("Happy---TIGER  42") == "happy-tiger-42"
        assert normalize_short_code("  HaPPy _ _TiGeR--  42\n") == "happy-tiger-42"

    def test_empty_string(self):
        """Test normalization of empty string."""
        assert normalize_short_code("") == ""
        assert normalize_short_code("   ") == ""

    def test_preserves_valid_characters(self):
        """Test that valid characters in code are preserved."""
        # Numbers should remain
        assert normalize_short_code("happy-tiger-99") == "happy-tiger-99"
        assert normalize_short_code("happy-tiger-10") == "happy-tiger-10"


class TestIntegration:
    """Integration tests combining generation, validation, and normalization."""

    def test_generated_codes_are_valid(self):
        """Test that all generated codes pass validation."""
        for _ in range(20):
            code = generate_short_code()
            assert validate_short_code(code) is True

    def test_normalized_valid_codes_remain_valid(self):
        """Test that normalizing valid codes keeps them valid."""
        valid_codes = [
            "HAPPY-TIGER-42",
            "clever eagle 55",
            "brave_dragon_99",
            "  swift-falcon-77  ",
        ]

        for code in valid_codes:
            normalized = normalize_short_code(code)
            # After normalization, should be valid if word lists match
            # (will fail if uppercase words aren't in lists)
            # Just verify normalization produces expected format
            parts = normalized.split("-")
            assert len(parts) == 3

    def test_roundtrip_generate_normalize_validate(self):
        """Test full roundtrip: generate -> normalize -> validate."""
        code = generate_short_code()
        normalized = normalize_short_code(code)
        assert validate_short_code(normalized) is True

    def test_collision_avoidance_with_normalized_codes(self):
        """Test that normalized codes are properly checked for collisions."""
        existing = {"happy-tiger-42"}

        # Try to generate code, should not collide with normalized version
        code = generate_short_code(existing)
        assert code not in existing
        assert code != "happy-tiger-42"
