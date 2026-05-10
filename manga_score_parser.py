#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from rect_repository import RectRepository

class RectSplitParser:
    def __init__(self, repo: RectRepository):
        self.repo = repo

    def parse_from_str(self, text: str, gap_v=5, gap_h=20):
        for line in text.splitlines():
            if not line.strip(): continue
            level = (len(line) - len(line.lstrip())) // 4
            content = line.strip()
            target = self.repo.get_target_at_level(level)
            if content.startswith('#'):
                match = re.match(r'#([vh])(\d+)', content)
                if match:
                    target.split(int(match.group(2))/100.0, match.group(1), gap_v, gap_h)
                    self.repo.push_to_stack(target)
            else:
                target.label = content






