import hashlib
import random
import string

def generate_unique_hash(comic_slug, chapter_num, group_type="Official"):
    """Generate a unique hash ID for each chapter based on real Comick patterns."""
    
    # Real examples from the HTML you provided:
    # SYgYVZds, Vr8Oudc_, rlKl2, 13oquvJEC, sTwO7_uA4laWl, Z91diXUG
    
    # Create a deterministic seed based on comic slug, chapter number, and group
    seed_string = f"{comic_slug}_{chapter_num}_{group_type}"
    
    # Use MD5 to create a consistent hash
    md5_hash = hashlib.md5(seed_string.encode()).hexdigest()
    
    # Take the first 8 characters and convert to base64-like characters
    # This creates a more realistic looking hash
    base_chars = string.ascii_letters + string.digits + '_'
    
    # Use the MD5 hash to select characters
    hash_id = ""
    for i in range(0, len(md5_hash), 2):
        if len(hash_id) >= 8:  # Target length of 8 characters
            break
        hex_pair = md5_hash[i:i+2]
        char_index = int(hex_pair, 16) % len(base_chars)
        hash_id += base_chars[char_index]
    
    # Ensure we have at least 5 characters
    if len(hash_id) < 5:
        hash_id += base_chars[random.randint(0, len(base_chars)-1)] * (5 - len(hash_id))
    
    return hash_id

def test_hash_generation():
    """Test the hash generation system."""
    comic_slug = "00-the-beginning-after-the-end-1"
    
    print("🔍 Testing unique hash generation...")
    
    # Test different chapters
    test_chapters = [0, 1, 2, 3, 4, 5, 10, 50, 100, 200, 225, 225.5]
    
    for chapter in test_chapters:
        hash_id = generate_unique_hash(comic_slug, chapter)
        print(f"Chapter {chapter}: {hash_id}")
    
    print("\n🔍 Testing consistency (same input should give same output)...")
    
    # Test consistency
    hash1 = generate_unique_hash(comic_slug, 1)
    hash2 = generate_unique_hash(comic_slug, 1)
    print(f"Chapter 1 (first call): {hash1}")
    print(f"Chapter 1 (second call): {hash2}")
    print(f"Consistent: {hash1 == hash2}")
    
    print("\n🔍 Testing uniqueness (different chapters should give different hashes)...")
    
    # Test uniqueness
    hashes = set()
    for i in range(100):
        hash_id = generate_unique_hash(comic_slug, i)
        hashes.add(hash_id)
    
    print(f"Generated 100 hashes, {len(hashes)} unique")
    print(f"Uniqueness: {len(hashes) == 100}")

if __name__ == "__main__":
    test_hash_generation()

