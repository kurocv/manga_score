#!/usr/bin/python
# -*- coding: utf-8 -*-

from manga_score_parser import RectSplitParser
from rect import Rect
from rect_repository import RectRepository
from PIL import Image, ImageDraw

class MangaScoreService:
    def __init__(self, width, height, line_width=1):
        self.width = width
        self.height = height
        self.line_width = line_width
        self.repo = RectRepository(width, height, line_width=line_width)
        self.current_index = 0

        # --- Undo用 ---
        self.history = []
        self.history_index = -1

    def get_current_index(self):
        return self.current_index
    def set_current_index(self, index):
        self.current_index = index
    def get_total_pages(self):
        return len(self.repo.roots)
    def get_current_root(self):
        if not self.repo.roots or self.current_index >= len(self.repo.roots):
            return None
        return self.repo.roots[self.current_index]
    def get_all_gap_rects(self) -> list:
        """現在表示中のページの全階層から、すべての隙間(gap_rect)をリストで取得する"""
        root = self.get_current_root()
        if not root:
            return []

        gaps = []
        self._collect_gaps_recursive(root, gaps)
        return gaps
    def _collect_gaps_recursive(self, node: Rect, gaps: list):
        """再帰的にノードを走査して gap_rect を集める内部関数"""
        if node.is_split:
            if node.gap_rect:
                gaps.append(node.gap_rect)
            
            # 子ノードを走査
            if node.orientation == 'v':
                if node.left: self._collect_gaps_recursive(node.left, gaps)
                if node.right: self._collect_gaps_recursive(node.right, gaps)
            else:
                if node.top: self._collect_gaps_recursive(node.top, gaps)
                if node.bottom: self._collect_gaps_recursive(node.bottom, gaps)

    def get_full_text(self):
        full_text = ""
        for r in self.repo.roots:
            full_text += r.dump_to_str(0) + "\n"
        return full_text.strip()
    def perform_parse(self, text):
        self.repo = RectRepository(self.width, self.height, line_width=self.line_width)
        parser = RectSplitParser(self.repo)
        parser.parse_from_str(text)
        
        if self.current_index >= len(self.repo.roots):
            self.current_index = max(0, len(self.repo.roots) - 1)

    def _draw_node_to_pil(self, draw, node):
        """PillowのDrawオブジェクトを使って再帰的に描画"""
        if not node.is_split:
            # 枠線の描画
            draw.rectangle(
                [node.x, node.y, node.x + node.w, node.y + node.h],
                outline="black",
                width=self.line_width
            )
            # ラベルがあれば描画（フォント設定は省略、デフォルト）
            if node.label:
                # 簡易的なテキスト配置（中央）
                draw.text((node.x + 5, node.y + 5), node.label, fill="black")
        else:
            # 子要素へ
            for child in [node.left, node.right, node.top, node.bottom]:
                # ※ 実際には orientation に合わせて node.left, node.right 等を呼ぶ
                if node.orientation == 'v':
                    self._draw_node_to_pil(draw, node.left)
                    self._draw_node_to_pil(draw, node.right)
                else:
                    self._draw_node_to_pil(draw, node.top)
                    self._draw_node_to_pil(draw, node.bottom)
                break # 再帰の重複防止（左右/上下を一度に呼ぶのでループは不要）

    def export_images(self):
        """全ページを個別のPNG画像として書き出す"""
        import os
        if not os.path.exists("export"):
            os.makedirs("export")

        for i, root_node in enumerate(self.repo.roots):
            # 1. 透明な画像を作成 (RGBA)
            img = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # 2. 再帰的に矩形を描画するヘルパー
            self._draw_node_to_pil(draw, root_node)
            
            # 3. 保存
            filename = f"export/page_{i+1:02d}.png"
            img.save(filename)
            print(f"Exported: {filename}")

        print("All pages exported to 'export' folder!")

    def console_output_layout(self, event):
        print("\n--- Current Layout Definition ---")
        full_text = self.get_full_text()
        print(full_text)
        print("----------------------------------")

    def save_history(self, text: str):
        """現在のテキストを履歴に保存"""
        text = text.strip()
        # 直前と同じなら保存しない
        if self.history and self.history[self.history_index] == text:
            return
        
        # Redo用履歴を削除して追加
        self.history = self.history[:self.history_index + 1]
        self.history.append(text)
        self.history_index += 1
        
        if len(self.history) > 100:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self) -> str:
        if self.history_index > 0:
            self.history_index -= 1
            return self.history[self.history_index]
        return None

    def redo(self) -> str:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index]
        return None
