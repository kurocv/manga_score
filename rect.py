#!/usr/bin/python
# -*- coding: utf-8 -*-

class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.is_split = False
        self.orientation = None
        self.ratio = None
        self.gap_rect = None  # 隙間部分の(x, y, w, h)を保持する
        self.left = self.right = self.top = self.bottom = None
        self.label = ""
    def __repr__(self):
        return f"Rect(x={self.x}, y={self.y}, w={self.w}, h={self.h}, label='{self.label}', is_split={self.is_split})"

    @property
    def is_blank(self):
        return not self.is_split and not self.label

    def split(self, ratio: float, orientation: str, gap_v=0, gap_h=0):
        self.is_split = True
        self.orientation = orientation
        self.ratio = ratio
        self.gap_v = gap_v
        self.gap_h = gap_h
        
        if orientation == 'v':
            # 縦分割（左右に並ぶ）→ 縦線の隙間(gap_v)を作る
            mid = int(self.w * ratio)
            half_gap = gap_v // 2
            
            # 左の右端を削り、右の左端を削る
            self.left = Rect(self.x, self.y, mid - half_gap, self.h)
            self.right = Rect(self.x + mid + half_gap, self.y, self.w - (mid + half_gap), self.h)
            # 隙間領域を記録（左の右端から、右の左端までの間）
            self.gap_rect = (self.x + mid - half_gap, self.y, gap_v, self.h)
            return self.left, self.right
        else:
            # 横分割（上下に並ぶ）→ 横線の隙間(gap_h)を作る
            mid = int(self.h * ratio)
            half_gap = gap_h // 2
            
            # 上の下端を削り、下の上の端を削る
            self.top = Rect(self.x, self.y, self.w, mid - half_gap)
            self.bottom = Rect(self.x, self.y + mid + half_gap, self.w, self.h - (mid + half_gap))
            # 隙間領域を記録（上の下端から、下の上端までの間）
            self.gap_rect = (self.x, self.y + mid - half_gap, self.w, gap_h)
            return self.top, self.bottom

    def recalculate(self):
        """親(自分)の座標サイズに基づき、隙間と子の座標をすべて再計算する"""
        if not self.is_split:
            return

        if self.orientation == 'v':
            mid = int(self.w * self.ratio)
            half_gap = self.gap_v // 2
            # 隙間の更新
            self.gap_rect = (self.x + mid - half_gap, self.y, self.gap_v, self.h)
            # 子の座標更新
            self.left.update_geometry(self.x, self.y, mid - half_gap, self.h)
            self.right.update_geometry(self.x + mid + half_gap, self.y, self.w - (mid + half_gap), self.h)
        else:
            mid = int(self.h * self.ratio)
            half_gap = self.gap_h // 2
            # 隙間の更新
            self.gap_rect = (self.x, self.y + mid - half_gap, self.w, self.gap_h)
            # 子の座標更新
            self.top.update_geometry(self.x, self.y, self.w, mid - half_gap)
            self.bottom.update_geometry(self.x, self.y + mid + half_gap, self.w, self.h - (mid + half_gap))

    def update_geometry(self, x, y, w, h):
        """自身のサイズを変更し、子がいたら連鎖的に再計算させる"""
        self.x, self.y, self.w, self.h = x, y, w, h
        if self.is_split:
            self.recalculate()

    def find_gap_parent(self, x, y):
        """クリック位置が隙間なら自分を返す。そうでなければ子を探す"""
        if not self.is_split: return None
        gx, gy, gw, gh = self.gap_rect
        if gx <= x <= gx + gw and gy <= y <= gy + gh:
            return self
        for child in [self.left, self.right, self.top, self.bottom]:
            if child:
                found = child.find_gap_parent(x, y)
                if found: return found
        return None

    def find_node_at(self, x, y):
        """指定座標にある末端のRect（Leaf）を返す"""
        if not self.is_split:
            if self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h:
                return self
            return None
        
        for child in [self.left, self.right, self.top, self.bottom]:
            if child:
                found = child.find_node_at(x, y)
                if found: return found
        return None

    def remove_children(self):
        """分割を解除して末端に戻す"""
        self.is_split = False
        self.gap_rect = None
        self.left = self.right = self.top = self.bottom = None
        # 子が持っていたラベルはどうするか？とりあえず空にするか、親が引き継ぐか
        # 今回はシンプルにリセット
        # self.label = ""

    def dump_to_str(self, level=0) -> str:
        """現在の構造をテキスト形式（#v50など）で書き出す"""
        indent = "    " * level
        res = []

        if self.is_split:
            # 分割命令の書き出し
            ratio_int = int(round(self.ratio * 100))
            res.append(f"{indent}#{self.orientation}{ratio_int}")
            
            # 子要素を再帰的に書き出す（パース時の埋まり順に合わせる）
            if self.orientation == 'v':
                # 右から先に処理していた仕様（reverseなし時）に合わせる
                res.append(self.right.dump_to_str(level + 1))
                res.append(self.left.dump_to_str(level + 1))
            else:
                # 上、下の順
                res.append(self.top.dump_to_str(level + 1))
                res.append(self.bottom.dump_to_str(level + 1))
        else:
            # ラベルの書き出し（空なら出力しないか、Emptyにするか選べますが、パース用なら空でない時のみ）
            if self.label:
                res.append(f"{indent}{self.label}")
            else:
                res.append(f"{indent}# Empty") # 構造確認用に空枠を表示

        return "\n".join([line for line in res if line.strip()])


