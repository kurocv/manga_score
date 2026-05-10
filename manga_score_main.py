# coding: UTF-8
# -*- coding: utf-8 -*-

import tkinter as tk
from manga_score_service import MangaScoreService
from manga_score_view_model import MangaScoreViewModel
from rect import Rect
import tkinter.simpledialog as sd

class MainView:
    def __init__(self, root, vm: MangaScoreViewModel, service: MangaScoreService):
        self.root = root
        self.vm = vm
        self.service = service
        self.parse_timer = None
        self.font = ("Consolas", 18)

        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0) # tearoff=0 で切り離し線を無効化
        file_menu.add_command(label="New", command=self.dummy)
        file_menu.add_command(label="Open...", command=self.dummy)
        file_menu.add_command(label="Save As...", command=self.dummy)
        file_menu.add_command(label="Export PNG", command=self.service.export_images)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.dummy)
        menubar.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menubar, tearoff=0) # tearoff=0 で切り離し線を無効化
        edit_menu.add_command(label="Flip horizontal", command=self.flip_horizontal)
        edit_menu.add_command(label="Paste", command=self.dummy)
        edit_menu.add_command(label="Delete", command=self.dummy)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(self.paned, width=40, font=("Consolas", 12))
        self.paned.add(self.text_area)

        self.canvas = tk.Canvas(self.paned, width=self.service.width, height=self.service.height, bg="white")
        self.paned.add(self.canvas)
        self.info_label = tk.Label(self.root, text="")
        self.info_label.pack()

        self.text_area.bind("<<Modified>>", self.on_text_modified)

        self.root.bind("<Control-Q>", lambda e: self.service.get_all_gap_rects())
        self.root.bind("<Control-W>", lambda e: self.service.get_current_root())

        self.root.bind("<Control-D>", lambda e: self.change_page(-1))
        self.root.bind("<Control-A>", lambda e: self.change_page(1))
        self.root.bind("<Control-S>", self.service.console_output_layout)
        # Undo/Redo バインド
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-y>", self.redo)
        self.root.bind("<Control-Shift-Z>", self.redo)

        self.canvas.bind("<Button-1>", self.on_click)               # 左：ドラッグ開始or横分割
        self.canvas.bind("<Double-Button-1>", self.on_double_click) # 左ダブル：削除or編集
        self.canvas.bind("<Button-2>", self.on_middle_click)        # 中：縦分割（Windows等は3の場合も）
        self.canvas.bind("<Button-3>", self.on_right_click)        # 右：縦分割（Windows等は3の場合も）

        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        initial_text = "#v50\n    aaa\n    bbb"
        self.text_area.insert("1.0", initial_text)
        self.service.save_history(initial_text)

    def on_closing(self):
        print("app 終了処理中...")
        self.vm.on_closing()
        self.root.destroy()

    def dummy(self):
        pass

    def flip_horizontal(self):
        self.service.toggle_flip_horizontal()
        self.perform_parse()

    def entry_select_all(self, event):
        event.widget.selection_range(0, tk.END)
        event.widget.icursor(0)

    def change_page(self, delta):
        if not self.service.get_total_pages(): return
        self.service.set_current_index((self.service.get_current_index() + delta) % self.service.get_total_pages())
        self.draw_page()

    def on_text_modified(self, event):
        """テキストが編集されたらパースを実行（タイマーで制御）"""
        if self.text_area.edit_modified():
            if self.parse_timer:
                self.root.after_cancel(self.parse_timer)
            self.parse_timer = self.root.after(300, self.perform_parse)
        self.text_area.edit_modified(False)

    def perform_parse(self):
        """テキストを読み込んで描画更新"""
        text = self.text_area.get("1.0", tk.END)
        # 現在のページ数を維持しつつ再構成
        self.service.perform_parse(text)
        self.draw_page()

    def draw_page(self):
        self.canvas.delete("all")
        
        current_root = self.service.get_current_root()
        if current_root is None:
            return
        self.draw_rect(current_root)
        self.info_label.config(text=f"Page: {self.service.get_current_index() + 1} / {self.service.get_total_pages()}")

    def draw_rect(self, node: Rect):
        # if node.is_split and node.gap_rect:
        #     self.canvas.create_rectangle(*self.rect_to_coords(node.gap_rect), fill="#eeeeee", outline="")

        if not node.is_split:
            self.canvas.create_rectangle(
                node.x, node.y, node.x + node.w, node.y + node.h,
                outline="black",
                width=self.service.line_width
            )


        if node.is_split:
            # 分割されている場合は子を再帰描画
            if node.orientation == 'v':
                self.draw_rect(node.left)
                self.draw_rect(node.right)
            else:
                self.draw_rect(node.top)
                self.draw_rect(node.bottom)
        elif node.label:
            # ラベルがある場合はテキスト描画
            self.canvas.create_text(
                node.x + node.w/2, node.y + node.h/2,
                text=node.label, fill="blue"
            )

    def on_click(self, event):
        # 1. 隙間のドラッグ開始判定（既存）
        current_root = self.service.get_current_root()
        self.dragging_node = current_root.find_gap_parent(event.x, event.y)
        if self.dragging_node: return

        # 2. 隙間以外なら、末端Rectを「横分割」
        target = current_root.find_node_at(event.x, event.y)
        if target:
            target.split(0.5, 'h', gap_h=20) # 50%で横分割
            self.draw_page()
            self.sync_to_text()
            self.service.save_history(self.text_area.get("1.0", tk.END))

    def on_middle_click(self, event):
        current_root = self.service.get_current_root()

        target = current_root.find_node_at(event.x, event.y)
        if target:
            new_label = sd.askstring("Label Edit", "Enter text:", initialvalue=target.label)
            if new_label is not None:
                target.label = new_label
                self.draw_page()
                self.sync_to_text()
                self.service.save_history(self.text_area.get("1.0", tk.END))

    def on_right_click(self, event):
        current_root = self.service.get_current_root()
        target = current_root.find_node_at(event.x, event.y)
        if target:
            target.split(0.5, 'v', gap_v=4) # 50%で縦分割
            self.draw_page()
            self.sync_to_text()
            self.service.save_history(self.text_area.get("1.0", tk.END))

    def on_double_click(self, event):
        current_root = self.service.get_current_root()

        # 1. 隙間をダブルクリックで「分割削除」
        gap_parent = current_root.find_gap_parent(event.x, event.y)
        if gap_parent:
            gap_parent.remove_children()
            self.draw_page()
            self.sync_to_text()
            self.service.save_history(self.text_area.get("1.0", tk.END))
            return

    def on_drag(self, event):
        if not self.dragging_node:
            return
        
        node = self.dragging_node
        # マウス位置から新しい比率を算出 (0.05〜0.95に制限して潰れを防止)
        if node.orientation == 'v':
            new_ratio = (event.x - node.x) / node.w
        else:
            new_ratio = (event.y - node.y) / node.h
            
        node.ratio = max(0.05, min(0.95, new_ratio))
        node.recalculate()  # 連鎖的な再計算
        self.draw_page()    # 再描画

    def on_release(self, event):
        if self.dragging_node:
            self.dragging_node = None
            self.sync_to_text()
            self.service.save_history(self.text_area.get("1.0", tk.END)) # 追加

    def rect_to_coords(self, r):
        # (x, y, w, h) -> (x1, y1, x2, y2) 変換用
        return (r[0], r[1], r[0] + r[2], r[1] + r[3])

    def sync_to_text(self):
        """Canvasの変更（ドラッグ等）をテキストエリアに反映"""
        # テキストエリアのイベントを一時停止して無限ループ防止
        self.text_area.edit_modified(False) 
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", self.service.get_full_text())
        self.text_area.edit_modified(False)

    def undo(self, event=None):
        text = self.service.undo()
        if text is not None:
            self._apply_text_from_logic(text)
        return "break"

    def redo(self, event=None):
        text = self.service.redo()
        if text is not None:
            self._apply_text_from_logic(text)
        return "break"

    def _apply_text_from_logic(self, text):
        """Serviceから戻ってきたテキストをTextエリアとCanvasに反映"""
        self.text_area.edit_modified(False)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", text)
        self.text_area.edit_modified(False) # ユーザー操作ではないのでFalseのまま
        self.perform_parse() # 描画も更新

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("+0+0")
    # root.geometry("1900x980+0+0")
    root.title("Manga Score Editor")

    service = MangaScoreService(int(2100//3.2), int(2970//3.2), line_width=1)
    vm = MangaScoreViewModel(service)

    app = MainView(root, vm, service)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()



