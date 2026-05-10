#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import List
from rect import Rect

class RectRepository:
    def __init__(self, canvas_w, canvas_h, outer_margin_v=50, outer_margin_h=50, line_width=2):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.outer_margin_v = outer_margin_v
        self.outer_margin_h = outer_margin_h
        self.line_width = line_width
        self.roots: List[Rect] = []
        self.stack: List[Rect] = []

    def set_level(self, level: int):
        while len(self.stack) > level:
            self.stack.pop()

    def get_target_at_level(self, level: int, reverse=False) -> Rect:
        self.set_level(level)
        if level == 0:
            new_root = Rect(
                self.outer_margin_h, 
                self.outer_margin_v, 
                self.canvas_w - (self.outer_margin_h * 2), 
                self.canvas_h - (self.outer_margin_v * 2)
            )
            self.roots.append(new_root)
            return new_root
        
        parent = self.stack[-1]
        if parent.orientation == 'v':
            if not reverse:
                if parent.right and parent.right.is_blank: return parent.right
                return parent.left
            else:
                if parent.left and parent.left.is_blank: return parent.left
                return parent.right
        else:
            if not reverse:
                if parent.top and parent.top.is_blank: return parent.top
                return parent.bottom
            else:
                if parent.bottom and parent.bottom.is_blank: return parent.bottom
                return parent.top

    def push_to_stack(self, rect: Rect):
        self.stack.append(rect)




