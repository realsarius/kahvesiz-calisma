import unittest

from scripts import seed_dev_data


class SeedReviewProfilesTests(unittest.TestCase):
    def test_profile_pick_is_deterministic(self):
        email = "zeynep@kahvesiz.local"
        first = seed_dev_data._pick_review_profile(email)
        second = seed_dev_data._pick_review_profile(email)
        self.assertEqual(first, second)

    def test_profile_rating_spans_full_scale(self):
        ratings = set()
        profiles = sorted(seed_dev_data.REVIEW_PROFILE_RATING_PATTERNS.keys())
        for cafe_index in range(25):
            for review_index, profile in enumerate(profiles):
                ratings.add(seed_dev_data._pick_profile_rating(profile, cafe_index, review_index))

        self.assertEqual(sorted(ratings), [1, 2, 3, 4, 5])

    def test_derived_sub_ratings_stay_in_range(self):
        for base in range(1, 6):
            for cafe_index in range(10):
                for review_index in range(10):
                    noise, wifi, outlet = seed_dev_data._derive_sub_ratings(base, cafe_index, review_index)
                    self.assertGreaterEqual(noise, 1)
                    self.assertLessEqual(noise, 5)
                    self.assertGreaterEqual(wifi, 1)
                    self.assertLessEqual(wifi, 5)
                    self.assertGreaterEqual(outlet, 1)
                    self.assertLessEqual(outlet, 5)

    def test_review_profiles_have_notes(self):
        profiles = set(seed_dev_data.REVIEW_PROFILE_RATING_PATTERNS.keys())
        note_profiles = {key for key, value in seed_dev_data.REVIEW_PROFILE_NOTES.items() if value.strip()}
        self.assertEqual(profiles, note_profiles)


if __name__ == "__main__":
    unittest.main()
