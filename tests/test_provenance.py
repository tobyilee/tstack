"""출처의 기록(`provenance.json`)을 검사한다. Spec 01의 목표 3, ADR-0002.

검사의 논리는 `scripts/provenance.py`에 있다 (ADR-0004 규칙 12).
테스트마다 둘이다: 이 저장소의 기록을 본다, 그리고 틀린 기록에서 검사가 문제를 찾는지 본다.
"""
import copy
import re
import unittest

import support

import provenance  # scripts/provenance.py. support가 scripts/를 import의 경로에 넣는다

ROOT = support.ROOT
COMMIT = "68fc5e24b76724b37dc9cc7e974121ea347c08ed"


def good_record():
    """문제가 없는 작은 기록. 틀린 기록은 이것을 고쳐서 만든다."""
    return {
        "source": {"repository": "https://github.com/tobyilee/trealworld", "commit": COMMIT},
        "files": [
            {"from": "tstack/README.md", "to": "plugins/tstack/README.md", "blob": "a" * 40, "changed": None},
            {"from": "tstack-guide.md", "to": "plugins/tstack/GUIDE.md", "blob": "b" * 40, "changed": "설치의 절을 고쳤다"},
        ],
    }


class Adr0002Rule3RecordExists(unittest.TestCase):
    def test_adr0002_3_record_is_at_the_repository_root(self):
        self.assertTrue(
            (ROOT / "provenance.json").is_file(),
            "ADR-0002 규칙 3: 저장소의 뿌리에 provenance.json이 없다",
        )

    def test_adr0002_3_loader_reads_the_record(self):
        record = provenance.load(ROOT)
        self.assertEqual(
            ["files", "source"], sorted(record),
            "ADR-0002 규칙 3: 기록의 맨 위의 키는 source와 files의 둘이어야 한다",
        )


class Ac3_1AllSourceFilesListed(unittest.TestCase):
    def test_ac3_1_record_lists_78_source_files(self):
        record = provenance.load(ROOT)
        self.assertEqual([], provenance.listing_problems(record, expected=78), "AC-3.1: 출처 파일 78개를 모두 나열해야 한다")

    def test_ac3_1_source_files_come_from_the_three_source_paths(self):
        record = provenance.load(ROOT)
        counts = provenance.count_by_source_path(record)
        self.assertEqual(
            {"tstack/": 34, ".claude/skills/explain-diff/": 43, "tstack-guide.md": 1}, counts,
            "AC-3.1: 출처 파일의 구성은 tstack 34개, explain-diff 43개, 가이드 1개다",
        )

    def test_ac3_1_checker_finds_a_missing_and_a_duplicate_entry(self):
        short = good_record()
        self.assertEqual(
            ["AC-3.1: 항목이 2개다. 3개여야 한다"], provenance.listing_problems(short, expected=3),
            "AC-3.1: 검사가 항목의 수가 모자란 것을 찾아야 한다",
        )
        twice = good_record()
        twice["files"].append(copy.deepcopy(twice["files"][0]))
        self.assertEqual(
            ["AC-3.1: from이 두 번 나온다: tstack/README.md", "AC-3.1: to가 두 번 나온다: plugins/tstack/README.md"],
            provenance.listing_problems(twice, expected=3),
            "AC-3.1: 검사가 같은 출처 파일과 같은 자리를 두 번 쓴 것을 찾아야 한다",
        )
        self.assertEqual([], provenance.listing_problems(good_record(), expected=2), "AC-3.1: 맞는 기록에는 문제가 없다")


class Ac3_3ChangedFilesHaveAReason(unittest.TestCase):
    def test_ac3_3_changed_entries_have_a_reason(self):
        record = provenance.load(ROOT)
        self.assertEqual([], provenance.reason_problems(record), "AC-3.3: 바꾼 파일마다 이유가 있어야 한다")

    def test_ac3_3_checker_finds_a_change_without_a_reason(self):
        for bad in ("", "   ", True, 1, []):
            record = good_record()
            record["files"][1]["changed"] = bad
            self.assertEqual(
                ["AC-3.3: 바꾼 이유가 글이 아니거나 비어 있다: plugins/tstack/GUIDE.md"],
                provenance.reason_problems(record),
                "AC-3.3: 검사가 이유가 %r 인 항목을 찾아야 한다" % (bad,),
            )
        self.assertEqual([], provenance.reason_problems(good_record()), "AC-3.3: null과 이유의 글은 허용이다")


class Ac3_4SourceIsRecorded(unittest.TestCase):
    def test_ac3_4_record_names_the_source_repository_and_commit(self):
        record = provenance.load(ROOT)
        self.assertEqual([], provenance.source_problems(record), "AC-3.4: 출처 저장소의 URL과 출처 커밋의 전체 해시가 있어야 한다")

    def test_ac3_4_commit_is_the_source_commit_of_the_domain_document(self):
        domain = (ROOT / "docs" / "domain" / "01-marketplace.md").read_text(encoding="utf-8")
        match = re.search(r"^\| 출처 커밋 \| `([0-9a-f]{40})` \|", domain, re.M)
        self.assertIsNotNone(match, "AC-3.4: Domain 01의 용어의 표에 출처 커밋의 줄이 없다")
        self.assertEqual(
            match.group(1), provenance.load(ROOT)["source"]["commit"],
            "AC-3.4: 기록의 커밋이 Domain 01의 출처 커밋과 같아야 한다",
        )

    def test_ac3_4_checker_finds_a_short_hash_and_a_wrong_url(self):
        short = good_record()
        short["source"]["commit"] = COMMIT[:7]
        self.assertEqual(
            ["AC-3.4: commit이 16진수 40자가 아니다: 68fc5e2"], provenance.source_problems(short),
            "AC-3.4: 검사가 짧은 해시를 찾아야 한다",
        )
        branch = good_record()
        branch["source"]["commit"] = "main"
        self.assertEqual(["AC-3.4: commit이 16진수 40자가 아니다: main"], provenance.source_problems(branch))
        no_url = good_record()
        no_url["source"]["repository"] = "tobyilee/trealworld"
        self.assertEqual(
            ["AC-3.4: repository가 https://github.com/ 의 URL이 아니다: tobyilee/trealworld"],
            provenance.source_problems(no_url),
            "AC-3.4: 검사가 URL이 아닌 값을 찾아야 한다",
        )
        missing = good_record()
        del missing["source"]["commit"]
        self.assertEqual(["AC-3.4: commit이 16진수 40자가 아니다: None"], provenance.source_problems(missing))
        self.assertEqual([], provenance.source_problems(good_record()), "AC-3.4: 맞는 기록에는 문제가 없다")


class Adr0002Rule4EntryShape(unittest.TestCase):
    def test_adr0002_4_entries_have_the_four_values(self):
        record = provenance.load(ROOT)
        self.assertEqual([], provenance.entry_problems(record), "ADR-0002 규칙 4: 항목마다 from, to, blob, changed가 있어야 한다")

    def test_adr0002_4_checker_finds_a_missing_value_and_a_bad_blob(self):
        no_key = good_record()
        del no_key["files"][0]["changed"]
        self.assertEqual(
            ["ADR-0002 규칙 4: 항목 1의 키가 from, to, blob, changed가 아니다: blob, from, to"],
            provenance.entry_problems(no_key),
            "ADR-0002 규칙 4: 검사가 빠진 값을 찾아야 한다. null과 '키가 없다'는 다르다",
        )
        bad_blob = good_record()
        bad_blob["files"][1]["blob"] = "xyz"
        self.assertEqual(
            ["ADR-0002 규칙 4: 항목 2의 blob이 16진수 40자가 아니다: xyz"], provenance.entry_problems(bad_blob),
            "ADR-0002 규칙 4: 검사가 git blob 해시가 아닌 값을 찾아야 한다",
        )
        outside = good_record()
        outside["files"][0]["to"] = "../elsewhere/README.md"
        self.assertEqual(
            ["ADR-0002 규칙 4: 항목 1의 to가 이 저장소의 안의 경로가 아니다: ../elsewhere/README.md"],
            provenance.entry_problems(outside),
            "ADR-0002 규칙 4: 검사가 저장소의 밖을 가리키는 자리를 찾아야 한다",
        )
        self.assertEqual([], provenance.entry_problems(good_record()), "ADR-0002 규칙 4: 맞는 기록에는 문제가 없다")


if __name__ == "__main__":
    unittest.main()
