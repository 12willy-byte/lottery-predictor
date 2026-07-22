import tkinter as tk
from tkinter import ttk,scrolledtext,messagebox
import threading
from collections import Counter
from itertools import combinations
from datetime import datetime

class LotteryGUI:
    def __init__(self,root):
        self.root=root
        self.root.title("彩票智能选号系统 v3.0")
        self.root.geometry("1200x780")
        self.root.minsize(1000,700)
        self.colors={"bg":"#f0f0f0","red":"#e74c3c","blue":"#3498db","front":"#e74c3c","back":"#2ecc71","gold":"#f39c12","dark":"#2c3e50","light_bg":"#ffffff","btn":"#3498db"}
        self.root.configure(bg=self.colors["bg"])
        self.ssq_data=[]; self.dlt_data=[]
        self.ssq_analysis=None; self.dlt_analysis=None
        self.ssq_backtest=None; self.dlt_backtest=None
        self.ssq_correction=None; self.dlt_correction=None
        self.ssq_base={}; self.dlt_base={}
        self.current_tab="ssq"
        try:
            from database import init_db,get_all_ssq,get_all_dlt
            init_db(); self.ssq_data=get_all_ssq(); self.dlt_data=get_all_dlt()
        except: pass
        self.setup_ui()
        self.update_status("SSQ:"+str(len(self.ssq_data))+" DLT:"+str(len(self.dlt_data)))
        if len(self.ssq_data)<50: self.root.after(500,self.auto_update)
        self.root.after(1000,self.auto_generate)
    def setup_ui(self):
        self.create_header()
        mf=tk.Frame(self.root,bg=self.colors["bg"]); mf.pack(fill=tk.BOTH,expand=True,padx=10,pady=(0,10))
        lp=tk.Frame(mf,bg=self.colors["light_bg"],relief=tk.RIDGE,bd=1); lp.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        self.create_tabs(lp)
        rp=tk.Frame(mf,bg=self.colors["light_bg"],relief=tk.RIDGE,bd=1,width=300); rp.pack(side=tk.RIGHT,fill=tk.BOTH,padx=(10,0)); rp.pack_propagate(False)
        self.create_right_panel(rp); self.create_statusbar()
    def create_header(self):
        h=tk.Frame(self.root,bg=self.colors["dark"],height=60); h.pack(fill=tk.X); h.pack_propagate(False)
        c=tk.Frame(h,bg=self.colors["dark"]); c.pack(expand=True)
        tk.Label(c,text="彩票智能选号系统",font=("微软雅黑",20,"bold"),bg=self.colors["dark"],fg="white").pack(side=tk.LEFT,padx=20)
        tk.Label(c,text="数据驱动 | 智能分析 | 科学选号",font=("微软雅黑",11),bg=self.colors["dark"],fg=self.colors["gold"]).pack(side=tk.LEFT)
        bf=tk.Frame(c,bg=self.colors["dark"]); bf.pack(side=tk.RIGHT,padx=15)
        self.create_btn=tk.Button(bf,text="更新数据",command=self.manual_update,font=("微软雅黑",10),bg=self.colors["btn"],fg="white",relief=tk.FLAT,padx=15,cursor="hand2")
        self.create_btn.pack(side=tk.LEFT,padx=5)
        self.backtest_btn=tk.Button(bf,text="回测分析",command=self.run_backtest,font=("微软雅黑",10),bg="#8e44ad",fg="white",relief=tk.FLAT,padx=15,cursor="hand2")
        self.backtest_btn.pack(side=tk.LEFT)
    def create_tabs(self,parent):
        tf=tk.Frame(parent,bg=self.colors["light_bg"]); tf.pack(fill=tk.X,padx=10,pady=(10,0))
        self.tab_ssq_btn=tk.Button(tf,text="双色球",font=("微软雅黑",12,"bold"),command=lambda:self.switch_tab("ssq"),bg=self.colors["red"],fg="white",relief=tk.FLAT,padx=20,cursor="hand2")
        self.tab_ssq_btn.pack(side=tk.LEFT,padx=(0,5))
        self.tab_dlt_btn=tk.Button(tf,text="大乐透",font=("微软雅黑",12,"bold"),command=lambda:self.switch_tab("dlt"),bg=self.colors["btn"],fg="white",relief=tk.FLAT,padx=20,cursor="hand2")
        self.tab_dlt_btn.pack(side=tk.LEFT)
        self.cf=tk.Frame(parent,bg=self.colors["light_bg"]); self.cf.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)
        self.create_ssq_view(); self.create_dlt_view(); self.show_ssq()
    def switch_tab(self,tab):
        self.current_tab=tab
        if tab=="ssq":
            self.ssq_frame.pack(fill=tk.BOTH,expand=True); self.dlt_frame.pack_forget()
            self.tab_ssq_btn.config(bg=self.colors["red"]); self.tab_dlt_btn.config(bg=self.colors["btn"])
        else:
            self.dlt_frame.pack(fill=tk.BOTH,expand=True); self.ssq_frame.pack_forget()
            self.tab_dlt_btn.config(bg=self.colors["back"]); self.tab_ssq_btn.config(bg=self.colors["btn"])
    def show_ssq(self): self.switch_tab("ssq")
    def show_dlt(self): self.switch_tab("dlt")
    def create_ssq_view(self):
        self.ssq_frame=tk.Frame(self.cf,bg=self.colors["light_bg"])
        sf=tk.Frame(self.ssq_frame,bg=self.colors["light_bg"]); sf.pack(fill=tk.X,pady=(0,10))
        self.ssq_stats=tk.Label(sf,text="等待分析...",font=("微软雅黑",10),bg=self.colors["light_bg"],fg=self.colors["dark"],anchor="w")
        self.ssq_stats.pack(fill=tk.X)
        df=tk.Frame(self.ssq_frame,bg=self.colors["light_bg"]); df.pack(fill=tk.BOTH,expand=True)
        self.ssq_rf=tk.LabelFrame(df,text="推荐号码",font=("微软雅黑",11,"bold"),bg=self.colors["light_bg"],padx=10,pady=10)
        self.ssq_rf.pack(fill=tk.BOTH,expand=True)
        self.ssq_cv=tk.Canvas(self.ssq_rf,bg=self.colors["light_bg"],highlightthickness=0)
        self.ssq_sb=tk.Scrollbar(self.ssq_rf,orient="vertical",command=self.ssq_cv.yview)
        self.ssq_sl=tk.Frame(self.ssq_cv,bg=self.colors["light_bg"])
        self.ssq_sl.bind("<Configure>",lambda e:self.ssq_cv.configure(scrollregion=self.ssq_cv.bbox("all")))
        self.ssq_cv.create_window((0,0),window=self.ssq_sl,anchor="nw")
        self.ssq_cv.configure(yscrollcommand=self.ssq_sb.set)
        self.ssq_cv.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); self.ssq_sb.pack(side=tk.RIGHT,fill=tk.Y)
        cf=tk.Frame(self.ssq_frame,bg=self.colors["light_bg"]); cf.pack(fill=tk.X,pady=(10,0))
        tk.Button(cf,text="生成推荐",command=self.generate_ssq,font=("微软雅黑",11,"bold"),bg=self.colors["red"],fg="white",relief=tk.FLAT,padx=30,cursor="hand2").pack(side=tk.LEFT,padx=5)
        self.ssq_cv2=tk.StringVar(value="1")
        tk.Spinbox(cf,from_=1,to=20,textvariable=self.ssq_cv2,width=5).pack(side=tk.LEFT,padx=5)
        tk.Label(cf,text="注",font=("微软雅黑",10),bg=self.colors["light_bg"]).pack(side=tk.LEFT)
        self.ssq_rec_label=tk.Label(self.ssq_frame,text="",font=("微软雅黑",8,"bold"),fg=self.colors["dark"],bg=self.colors["light_bg"],anchor="w")
        self.ssq_rec_label.pack(fill=tk.X,padx=10,pady=(2,0))
        self.ssq_legend=tk.Label(self.ssq_frame,text="",font=("微软雅黑",7),fg="gray",bg=self.colors["light_bg"],anchor="w")
        self.ssq_legend.pack(fill=tk.X,padx=10,pady=(2,0))
    def create_dlt_view(self):
        self.dlt_frame=tk.Frame(self.cf,bg=self.colors["light_bg"])
        sf=tk.Frame(self.dlt_frame,bg=self.colors["light_bg"]); sf.pack(fill=tk.X,pady=(0,10))
        self.dlt_stats=tk.Label(sf,text="等待分析...",font=("微软雅黑",10),bg=self.colors["light_bg"],fg=self.colors["dark"],anchor="w")
        self.dlt_stats.pack(fill=tk.X)
        df=tk.Frame(self.dlt_frame,bg=self.colors["light_bg"]); df.pack(fill=tk.BOTH,expand=True)
        self.dlt_rf=tk.LabelFrame(df,text="推荐号码",font=("微软雅黑",11,"bold"),bg=self.colors["light_bg"],padx=10,pady=10)
        self.dlt_rf.pack(fill=tk.BOTH,expand=True)
        self.dlt_cv=tk.Canvas(self.dlt_rf,bg=self.colors["light_bg"],highlightthickness=0)
        self.dlt_sb=tk.Scrollbar(self.dlt_rf,orient="vertical",command=self.dlt_cv.yview)
        self.dlt_sl=tk.Frame(self.dlt_cv,bg=self.colors["light_bg"])
        self.dlt_sl.bind("<Configure>",lambda e:self.dlt_cv.configure(scrollregion=self.dlt_cv.bbox("all")))
        self.dlt_cv.create_window((0,0),window=self.dlt_sl,anchor="nw")
        self.dlt_cv.configure(yscrollcommand=self.dlt_sb.set)
        self.dlt_cv.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); self.dlt_sb.pack(side=tk.RIGHT,fill=tk.Y)
        cf=tk.Frame(self.dlt_frame,bg=self.colors["light_bg"]); cf.pack(fill=tk.X,pady=(10,0))
        tk.Button(cf,text="生成推荐",command=self.generate_dlt,font=("微软雅黑",11,"bold"),bg=self.colors["front"],fg="white",relief=tk.FLAT,padx=30,cursor="hand2").pack(side=tk.LEFT,padx=5)
        self.dlt_cv2=tk.StringVar(value="1")
        tk.Spinbox(cf,from_=1,to=20,textvariable=self.dlt_cv2,width=5).pack(side=tk.LEFT,padx=5)
        tk.Label(cf,text="注",font=("微软雅黑",10),bg=self.colors["light_bg"]).pack(side=tk.LEFT)
    def create_right_panel(self,parent):
        inf=tk.LabelFrame(parent,text="数据概览",font=("微软雅黑",11,"bold"),bg=self.colors["light_bg"],padx=10,pady=10)
        inf.pack(fill=tk.X,padx=10,pady=10)
        self.di=tk.Text(inf,height=8,font=("微软雅黑",9),bg=self.colors["light_bg"],relief=tk.FLAT)
        self.di.pack(fill=tk.X); self.di.insert(tk.END,"加载中..."); self.di.config(state=tk.DISABLED)
        bzf=tk.LabelFrame(parent,text="后区预测",font=("微软雅黑",11,"bold"),bg=self.colors["light_bg"],padx=10,pady=10)
        bzf.pack(fill=tk.X,padx=10,pady=(0,10))
        self.bz_text=tk.Text(bzf,height=10,font=("微软雅黑",9),bg=self.colors["light_bg"],relief=tk.FLAT)
        self.bz_text.pack(fill=tk.X); self.bz_text.insert(tk.END,"分析中..."); self.bz_text.config(state=tk.DISABLED)
        rf2=tk.LabelFrame(parent,text="最近开奖",font=("微软雅黑",11,"bold"),bg=self.colors["light_bg"],padx=10,pady=10)
        rf2.pack(fill=tk.BOTH,expand=True,padx=10,pady=(0,10))
        self.rt=scrolledtext.ScrolledText(rf2,height=10,font=("微软雅黑",9),bg=self.colors["light_bg"],relief=tk.FLAT)
        self.rt.pack(fill=tk.BOTH,expand=True)
    def create_statusbar(self):
        sf=tk.Frame(self.root,bg=self.colors["dark"],height=28); sf.pack(fill=tk.X); sf.pack_propagate(False)
        self.sl=tk.Label(sf,text="就绪",font=("微软雅黑",9),bg=self.colors["dark"],fg="white",anchor="w")
        self.sl.pack(side=tk.LEFT,padx=15)
        self.pl=tk.Label(sf,text="",font=("微软雅黑",9),bg=self.colors["dark"],fg=self.colors["gold"],anchor="e")
        self.pl.pack(side=tk.RIGHT,padx=15)
    def update_status(self,text,prog=""): self.sl.config(text=text); self.pl.config(text=prog); self.root.update_idletasks()
    def update_backzone(self):
        try:
            from collections import Counter
            from database import get_all_ssq, get_all_dlt
            ssq = get_all_ssq(); dlt = get_all_dlt()
            if not ssq or not dlt: return
            blues = [d["blue"] for d in ssq]
            backs = [(d["back1"], d["back2"]) for d in dlt]
            follow = {}
            for i in range(1, len(blues)):
                prev = blues[i-1]
                if prev not in follow: follow[prev] = Counter()
                follow[prev][blues[i]] += 1
            prev_blue = blues[-1]
            om_blue = {}
            for n in range(1, 17):
                if n == prev_blue: om_blue[n] = 0
                else:
                    c = 0
                    for b in reversed(blues[:-1]):
                        if b == n: break
                        c += 1
                    om_blue[n] = c + 1
            freq_blue = Counter(blues[-100:])
            mixed_blue = {}
            for n in range(1, 17):
                mixed_blue[n] = freq_blue.get(n,0)*0.4 + om_blue[n]*0.3
                if prev_blue in follow and sum(follow[prev_blue].values())>0:
                    mixed_blue[n] += follow[prev_blue].get(n,0)/sum(follow[prev_blue].values())*30
            top_blue = sorted(mixed_blue, key=lambda n:-mixed_blue[n])[:5]
            follow_top = []
            if prev_blue in follow:
                follow_top = [n for n,_ in follow[prev_blue].most_common(3)]
            # === DLT后区 (v3.1: 频率0.8:遗漏0.2 + 重号 + 跟随) ===
            flat_backs = [b for p in backs for b in p]
            freq_back = Counter(flat_backs)
            latest_back = backs[-1]
            # 遗漏
            om_back = {}
            for n in range(1, 13):
                if n in latest_back: om_back[n] = 0
                else:
                    c = 0
                    for p in reversed(backs[:-1]):
                        if n in p: break
                        c += 1
                    om_back[n] = c + 1
            # 后区跟随统计
            back_follow = {}
            for i in range(1, len(backs)):
                for pb in backs[i-1]:
                    if pb not in back_follow: back_follow[pb] = Counter()
                    for nb in backs[i]:
                        back_follow[pb][nb] += 1
            # 重号率
            repeat_count = sum(1 for i in range(1, len(backs)) if set(backs[i]) & set(backs[i-1]))
            repeat_rate = repeat_count / max(len(backs)-1, 1)
            scores_back = {}
            for n in range(1, 13):
                scores_back[n] = freq_back.get(n,0) * 0.8 + om_back.get(n,0) * 0.2
                # 跟随加分
                for lb in latest_back:
                    if lb in back_follow and sum(back_follow[lb].values()) > 0:
                        scores_back[n] += back_follow[lb].get(n,0) / sum(back_follow[lb].values()) * 8
                # 重号加分
                if n in latest_back:
                    scores_back[n] += repeat_rate * 15
            top_back = sorted(scores_back, key=lambda n:-scores_back[n])[:6]
            # 组合评分（移除奇偶惩罚，无数据支持）
            best_pairs = []
            for a in top_back:
                for b in top_back:
                    if a < b:
                        sc = scores_back[a] + scores_back[b]
                        s2 = a + b
                        if 7 <= s2 <= 17: sc *= 1.05
                        best_pairs.append(((a,b), round(sc,1)))
            best_pairs.sort(key=lambda x: -x[1])
            text = "SSQ蓝球推荐 (命中期望~9%):\n"
            text += "  综合: %s\n" % top_blue
            if follow_top:
                text += "  跟随(上期%d): %s\n" % (prev_blue, follow_top)
            text += "\nDLT后区推荐 (命中期望~0.35/2):\n"
            text += "  单号: %s\n" % top_back
            text += "  上期: (%d,%d) 重号率%.0f%%\n" % (latest_back[0], latest_back[1], repeat_rate*100)
            for i, ((a,b),sc) in enumerate(best_pairs[:4]):
                repeat_mark = " \u2605\u91cd" if (a in latest_back or b in latest_back) else ""
                text += "  #%d: (%2d,%2d)%.0f%s\n" % (i+1, a, b, sc, repeat_mark)
            self.bz_text.config(state=tk.NORMAL)
            self.bz_text.delete(1.0, tk.END)
            self.bz_text.insert(tk.END, text)
            self.bz_text.config(state=tk.DISABLED)
        except: pass
    def draw_ball(self,parent,num,color,size=36):
        f=tk.Frame(parent,bg=self.colors["light_bg"]); f.pack(side=tk.LEFT,padx=3)
        c=tk.Canvas(f,width=size+2,height=size+2,bg=self.colors["light_bg"],highlightthickness=0); c.pack()
        c.create_oval(3,3,size+2,size+2,fill="#cccccc",outline="")
        c.create_oval(1,1,size,size,fill=color,outline="white",width=1.5)
        
        c.create_text(size//2+1,size//2+1,text=str(num),fill="white",font=("Arial",size//3,"bold"))
    def display_ssq_result(self,preds):
        for w in self.ssq_sl.winfo_children(): w.destroy()
        if not preds:
            tk.Label(self.ssq_sl,text="暂无推荐",font=("微软雅黑",12),bg=self.colors["light_bg"],fg="gray").pack(pady=50); return
        for pred in preds:
            row=tk.Frame(self.ssq_sl,bg=self.colors["light_bg"]); row.pack(fill=tk.X,pady=4)
            period_text=pred.get("period","未知")
            label=period_text+" "+("★" if pred.get("corrected") else "")
            fg_c="#8e44ad" if pred.get("corrected") else self.colors["dark"]
            lbl=tk.Label(row,text=label,font=("微软雅黑",9,"bold"),fg=fg_c,bg=self.colors["light_bg"])
            lbl.pack(side=tk.LEFT,padx=5)
            rf=tk.Frame(row,bg=self.colors["light_bg"]); rf.pack(side=tk.LEFT,padx=2)
            for n in pred["reds"]: self.draw_ball(rf,n,self.colors["red"],30)
            bf=tk.Frame(row,bg=self.colors["light_bg"]); bf.pack(side=tk.LEFT,padx=5)
            self.draw_ball(bf,pred["blue"],self.colors["blue"],30)
            score=pred.get("score",0)
            is_corrected=pred.get("corrected",False)
            lbl2_label="评分:"+str(score)
            if is_corrected:
                lbl2_label+=" (偏差修正)"
            lbl2=tk.Label(row,text=lbl2_label,font=("微软雅黑",7),fg="#8e44ad" if is_corrected else "gray",bg=self.colors["light_bg"])
            lbl2.pack(side=tk.LEFT,padx=3)
            # 策略明细
            det=pred.get("detail",{})
            if det and not is_corrected:
                det_items=[k+"="+str(v) for k,v in det.items() if isinstance(v,(int,float)) and v!=0]
                det_text=" | ".join(det_items[:8])
                if len(det_items)>8:
                    det_text+="..."
                det_lbl=tk.Label(row,text=det_text,font=("微软雅黑",6),fg="#7f8c8d",bg=self.colors["light_bg"])
                det_lbl.pack(side=tk.LEFT,padx=2)
    
    def show_v54_badge(self, parent, row, col):
        """Show V5.4 CRF prediction badge"""
        import tkinter as tk
        badge = tk.Label(parent, text="V5.4 CRF", font=("微软雅黑", 7, "bold"),
                        bg="#ff6600", fg="white", padx=3, pady=1)
        badge.grid(row=row, column=col, sticky="w", padx=(2,0))

    def display_dlt_result(self,preds):
        for w in self.dlt_sl.winfo_children(): w.destroy()
        if not preds:
            tk.Label(self.dlt_sl,text="暂无推荐",font=("微软雅黑",12),bg=self.colors["light_bg"],fg="gray").pack(pady=50); return
        for pred in preds:
            row=tk.Frame(self.dlt_sl,bg=self.colors["light_bg"]); row.pack(fill=tk.X,pady=4)
            period_text=pred.get("period","未知")
            label=period_text+" "+("★" if pred.get("corrected") else "")
            fg_c="#8e44ad" if pred.get("corrected") else self.colors["dark"]
            lbl=tk.Label(row,text=label,font=("微软雅黑",9,"bold"),fg=fg_c,bg=self.colors["light_bg"])
            lbl.pack(side=tk.LEFT,padx=5)
            ff=tk.Frame(row,bg=self.colors["light_bg"]); ff.pack(side=tk.LEFT,padx=2)
            for n in pred["fronts"]: self.draw_ball(ff,n,self.colors["front"],30)
            bf2=tk.Frame(row,bg=self.colors["light_bg"]); bf2.pack(side=tk.LEFT,padx=5)
            for n in pred["backs"]: self.draw_ball(bf2,n,self.colors["back"],30)
            score=pred.get("score",0)
            is_corrected=pred.get("corrected",False)
            lbl2_label="评分:"+str(score)
            if is_corrected:
                lbl2_label+=" (偏差修正)"
            lbl2=tk.Label(row,text=lbl2_label,font=("微软雅黑",7),fg="#8e44ad" if is_corrected else "gray",bg=self.colors["light_bg"])
            lbl2.pack(side=tk.LEFT,padx=3)
            # 策略明细
            det=pred.get("detail",{})
            if det and not is_corrected:
                det_items=[k+"="+str(v) for k,v in det.items() if isinstance(v,(int,float)) and v!=0]
                det_text=" | ".join(det_items[:8])
                if len(det_items)>8:
                    det_text+="..."
                det_lbl=tk.Label(row,text=det_text,font=("微软雅黑",6),fg="#7f8c8d",bg=self.colors["light_bg"])
                det_lbl.pack(side=tk.LEFT,padx=2)
    def manual_update(self):
        self.update_status("更新中...")
        self.create_btn.config(state=tk.DISABLED,text="更新中...")
        def do_upd():
            try:
                from data_scraper import update_all
                import io,sys
                old=sys.stdout; sys.stdout=buf=io.StringIO()
                try: update_all(callback=lambda s,st,m: None)
                except: update_all()
                sys.stdout=old
                from database import get_all_ssq,get_all_dlt
                self.ssq_data=get_all_ssq(); self.dlt_data=get_all_dlt()
                self.root.after(0,self.on_upd_ok)
            except Exception as e:
                self.root.after(0,lambda:self.on_upd_err(str(e)))
        threading.Thread(target=do_upd,daemon=True).start()
    def on_upd_ok(self):
        self.create_btn.config(state=tk.NORMAL,text="更新数据")
        self.update_data_info(); self.update_recent()
        self.update_backzone()
        self.update_status("已更新 | SSQ:"+str(len(self.ssq_data))+" DLT:"+str(len(self.dlt_data)))
        self.auto_analyze()
    def on_upd_err(self,err):
        self.create_btn.config(state=tk.NORMAL,text="更新数据")
        messagebox.showerror("更新失败",str(err))
    def auto_update(self): self.manual_update()
    def auto_generate(self):
        try:
            self.auto_analyze()
            if self.ssq_analysis: self.generate_ssq()
            if self.dlt_analysis: self.generate_dlt()
            self.update_backzone()
            self.update_status("自动生成完成")
        except:
            pass
    def auto_analyze(self):
        try:
            from analyzer import SSQAnalyzer,DLTAnalyzer
            if self.ssq_data:
                a=SSQAnalyzer(self.ssq_data); self.ssq_analysis=a.comprehensive_analysis(); self.upd_ssq_stats()
            if self.dlt_data:
                a=DLTAnalyzer(self.dlt_data); self.dlt_analysis=a.comprehensive_analysis(); self.upd_dlt_stats()
            self._load_backtest_cache()
        except: pass

    def _load_backtest_cache(self):
        import os, json
        cf=os.path.join("data","backtest_cache.json")
        if os.path.exists(cf):
            with open(cf,"r",encoding="utf-8") as f:
                c=json.load(f)
            if "ssq" in c: self.ssq_correction=c["ssq"].get("correction")
            if "dlt" in c: self.dlt_correction=c["dlt"].get("correction")

    def run_backtest(self):
        self.backtest_btn.config(state=tk.DISABLED, text="回测中...")
        def do():
            try:
                from backtester import fast_analysis, predict_main
                import json, os
                result={}
                if self.ssq_data and len(self.ssq_data)>100:
                    data=self.ssq_data[-200:]
                    res=[]
                    for i in range(50,len(data)-1):
                        train=data[:i+1]; actual=data[i+1]
                        anl=fast_analysis(train,"ssq")
                        pn,pb=predict_main(anl,33,6,16,1)
                        ah={actual["red%d"%j] for j in range(1,7)}
                        hit=len(set(pn)&ah)
                        aso=sorted([actual["red%d"%j] for j in range(1,7)])
                        pbias=[aso[k]-pn[k] for k in range(6)]
                        res.append({"hit":hit,"pos_biases":pbias})
                    n=len(res)
                    if n>0:
                        hd=Counter(r["hit"] for r in res)
                        ab=[round(sum(r["pos_biases"][j] for r in res)/n,2) for j in range(6)]
                        cv=[round(b) for b in ab]
                        self.ssq_correction={"values":cv} if max(abs(b) for b in ab)>=0.7 else None
                        result["ssq"]={"total":n,"hit_dist":{str(k):round(v/n*100,1) for k,v in sorted(hd.items())},"avg_bias":ab,"correction":self.ssq_correction}
                        self.root.after(0,lambda: self.ssq_stats.config(text="SSQ回测: %d\u6b21 \u547d\u4e2d:%s \u504f\u5dee:%s"%(n,str(dict(sorted(hd.items()))),str(ab))))
                if self.dlt_data and len(self.dlt_data)>100:
                    data=self.dlt_data[-200:]
                    res=[]
                    for i in range(50,len(data)-1):
                        train=data[:i+1]; actual=data[i+1]
                        anl=fast_analysis(train,"dlt")
                        pn,pb=predict_main(anl,35,5,12,2)
                        ah={actual["front%d"%j] for j in range(1,6)}
                        hit=len(set(pn)&ah)
                        aso=sorted([actual["front%d"%j] for j in range(1,6)])
                        pbias=[aso[k]-pn[k] for k in range(5)]
                        res.append({"hit":hit,"pos_biases":pbias})
                    n=len(res)
                    if n>0:
                        hd=Counter(r["hit"] for r in res)
                        ab=[round(sum(r["pos_biases"][j] for r in res)/n,2) for j in range(5)]
                        cv=[round(b) for b in ab]
                        self.dlt_correction={"values":cv} if max(abs(b) for b in ab)>=0.7 else None
                        result["dlt"]={"total":n,"hit_dist":{str(k):round(v/n*100,1) for k,v in sorted(hd.items())},"avg_bias":ab,"correction":self.dlt_correction}
                        self.root.after(0,lambda: self.dlt_stats.config(text="DLT回测: %d\u6b21 \u547d\u4e2d:%s \u504f\u5dee:%s"%(n,str(dict(sorted(hd.items()))),str(ab))))
                import json, os
                with open(os.path.join("data","backtest_cache.json"),"w",encoding="utf-8") as f:
                    json.dump(result,f,ensure_ascii=False)
                self.root.after(0,self._on_backtest_done)
            except Exception as e:
                self.root.after(0,lambda: self._on_backtest_err(str(e)))
        import threading
        threading.Thread(target=do,daemon=True).start()

    def _on_backtest_done(self):
        self.backtest_btn.config(state=tk.NORMAL,text="回测分析")
        from database import get_latest_ssq, get_latest_dlt
        txt="回测完成"
        if self.ssq_correction:
            last=get_latest_ssq()
            np=str(int(last["period"])+1) if last else "??"
            txt+=" | SSQ第"+np+"期修正: "+" ".join(["%+d"%c for c in self.ssq_correction["values"]])
        if self.dlt_correction:
            last=get_latest_dlt()
            np=str(int(last["period"])+1) if last else "??"
            txt+=" | DLT第"+np+"期修正: "+" ".join(["%+d"%c for c in self.dlt_correction["values"]])
        self.update_status(txt)
        if self.current_tab=="ssq": self.generate_ssq()
        else: self.generate_dlt()

    def _update_ssq_legend(self):
        try:
            ts=self.ssq_analysis.get("tail_stats",{}); ss=self.ssq_analysis.get("span_stats",{}); rs=self.ssq_analysis.get("rn_stats",{})
            w=ts.get("avg_unique_tails",0); s=ss.get("most_common_span",0); r=rs.get("avg_repeat",0)
            self.ssq_legend.config(text="16维策略: 冷热18+遗漏14+尾数12+跨度8+奇偶8+大小8+跟随8+重邻孤8(基础92) | 012路6+均值回归5+边码5+模式匹配6+动量4+遗漏回补5+周期4+黄金3(新增38) | 质数+AC+和值+位置+振幅+间隔+波动(加分~90) | 尾数"+str(w)+"种 跨度"+str(s)+" 重号"+str(r))
        except: pass

    def _on_backtest_err(self,err):
        self.backtest_btn.config(state=tk.NORMAL,text="回测分析")
        messagebox.showerror("回测失败",err)
    def upd_ssq_stats(self):
        if not self.ssq_analysis: return
        a=self.ssq_analysis
        hc=len(a["red_hot_cold"]["hot"]); wc=len(a["red_hot_cold"]["warm"]); cc=len(a["red_hot_cold"]["cold"])
        text="分析:"+str(a["total"])+"期 H:"+str(hc)+" W:"+str(wc)+" C:"+str(cc)
        if self.ssq_correction and "values" in self.ssq_correction:
            text+=" | 修正: "+" ".join(["%+d"%c for c in self.ssq_correction["values"]])
        self.ssq_stats.config(text=text)
    def upd_dlt_stats(self):
        if not self.dlt_analysis: return
        a=self.dlt_analysis
        hc=len(a["front_hot_cold"]["hot"]); wc=len(a["front_hot_cold"]["warm"]); cc=len(a["front_hot_cold"]["cold"])
        text="分析:"+str(a["total"])+"期 H:"+str(hc)+" W:"+str(wc)+" C:"+str(cc)
        if self.dlt_correction and "values" in self.dlt_correction:
            text+=" | 修正: "+" ".join(["%+d"%c for c in self.dlt_correction["values"]])
        self.dlt_stats.config(text=text)
    def generate_ssq(self):
        if not self.ssq_analysis: self.auto_analyze()
        if not self.ssq_analysis: return
        try: cnt=int(self.ssq_cv2.get())
        except: cnt=5
        from analyzer import MultiStrategyPredictor, SSQAnalyzer
        from database import get_latest_ssq
        last=get_latest_ssq()
        next_period=str(int(last["period"])+1) if last else "???"
        msp=MultiStrategyPredictor()
        import json, os
        cache_path=os.path.join("data","weights_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path,"r",encoding="utf-8") as _f:
                _c=json.load(_f)
            if "ssq" in _c:
                msp.weights.update(_c["ssq"])
        else:
            msp.self_evaluate("ssq",self.ssq_data)
            with open(cache_path,"w",encoding="utf-8") as _f:
                json.dump({"ssq":dict(msp.weights)},_f)
        self.ssq_base=dict(msp.weights)
        anl=SSQAnalyzer(self.ssq_data).comprehensive_analysis()
        if self.ssq_correction:
            anl["_correction"]=self.ssq_correction
        preds=msp.select_best_ssq(anl, count=3, period_seed=next_period)
        self.ssq_preds=[]
        if preds:
            for idx, pred in enumerate(preds):
                label = next_period if idx == 0 else f"{next_period}-{idx+1}"
                self.ssq_preds.append({"period":label,"reds":pred["reds"],"blue":pred["blue"],"score":pred.get("score",0),"detail":pred.get("detail",{})})
        self.ssq_rec_title="推荐: 全量候选池16维(共%d组)" % len(preds)
        if self.ssq_correction:
            corr=self.ssq_correction.get("values")
            if corr and max(abs(c) for c in corr)>=1 and preds:
                cr=sorted([max(1,min(33,preds[0]["reds"][j]+corr[j])) for j in range(6)])
                if len(set(cr))==6:
                    cr_score=preds[0].get("score",0)-3
                    self.ssq_preds.append({"period":next_period+"*","reds":cr,"blue":preds[0]["blue"],"score":cr_score,"corrected":True,"detail":{}})
                    self.ssq_rec_title+=" [偏差修正版]"
        self.display_ssq_result(self.ssq_preds)
        # V5.4 CRF Engine integration
        try:
            from v54_engine import predict_ssq as predict_ssq_v54
            v54_preds = predict_ssq_v54(3)
            self.ssq_preds_v54 = []
            for idx, p in enumerate(v54_preds):
                label = next_period + "-V54" if idx == 0 else f"{next_period}-V54-{idx+1}"
                self.ssq_preds_v54.append({"period": label, "reds": p["reds"], "blue": p["blue"], "score": p["score"]})
        except Exception as e:
            self.ssq_preds_v54 = []
        txt="SSQ第%s期" % next_period
        if self.ssq_correction: txt+=" [策略投票+偏差修正]"
        self.update_status(txt)
        self._update_ssq_legend()
        # 推荐说明
        if hasattr(self,"ssq_rec_label"):
            self.ssq_rec_label.config(text=self.ssq_rec_title)
    def generate_dlt(self):
        if not self.dlt_analysis: self.auto_analyze()
        if not self.dlt_analysis: return
        try: cnt=int(self.dlt_cv2.get())
        except: cnt=5
        from analyzer import MultiStrategyPredictor, DLTAnalyzer
        from database import get_latest_dlt
        last=get_latest_dlt()
        next_period=str(int(last["period"])+1) if last else "???"
        msp=MultiStrategyPredictor()
        import json, os
        cache_path=os.path.join("data","weights_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path,"r",encoding="utf-8") as _f:
                _c=json.load(_f)
            if "dlt" in _c:
                msp.weights.update(_c["dlt"])
        else:
            msp.self_evaluate("dlt",self.dlt_data)
            with open(cache_path,"w",encoding="utf-8") as _f:
                json.dump({"dlt":dict(msp.weights)},_f)
        self.dlt_base=dict(msp.weights)
        anl=DLTAnalyzer(self.dlt_data).comprehensive_analysis()
        if self.dlt_correction:
            anl["_correction"]=self.dlt_correction
        preds=msp.select_best_dlt(anl, count=3, period_seed=next_period)
        self.dlt_preds=[]
        if preds:
            for idx, pred in enumerate(preds):
                label = next_period if idx == 0 else f"{next_period}-{idx+1}"
                self.dlt_preds.append({"period":label,"fronts":pred["fronts"],"backs":pred["backs"],"score":pred.get("score",0),"detail":pred.get("detail",{})})
        self.dlt_rec_title="推荐: 全量候选池16维(共%d组)" % len(preds)
        if self.dlt_correction:
            corr=self.dlt_correction.get("values")
            if corr and max(abs(c) for c in corr)>=1 and preds:
                cr=sorted([max(1,min(35,preds[0]["fronts"][j]+corr[j])) for j in range(5)])
                if len(set(cr))==5:
                    cr_score=preds[0].get("score",0)-3
                    self.dlt_preds.append({"period":next_period+"*","fronts":cr,"backs":preds[0]["backs"],"score":cr_score,"corrected":True,"detail":{}})
                    self.dlt_rec_title+=" [偏差修正版]"
        self.display_dlt_result(self.dlt_preds)
        # V5.4 CRF Engine integration
        try:
            from v54_engine import predict_dlt as predict_dlt_v54
            v54_preds_d = predict_dlt_v54(3)
            self.dlt_preds_v54 = []
            for idx, p in enumerate(v54_preds_d):
                label = next_period + "-V54" if idx == 0 else f"{next_period}-V54-{idx+1}"
                self.dlt_preds_v54.append({"period": label, "reds": p["reds"], "blues": p["blues"], "score": p["score"]})
        except Exception as e:
            self.dlt_preds_v54 = []
        txt="DLT第%s期" % next_period
        if self.dlt_correction: txt+=" [策略投票+偏差修正]"
        self.update_status(txt)
        if hasattr(self,"dlt_rec_label"):
            self.dlt_rec_label.config(text=self.dlt_rec_title)
        # DLT legend
        try:
            ts=self.dlt_analysis.get("tail_stats",{}); ss=self.dlt_analysis.get("span_stats",{}); rs=self.dlt_analysis.get("rn_stats",{})
            w=ts.get("avg_unique_tails",0); s=ss.get("most_common_span",0); r=rs.get("avg_repeat",0)
            self.dlt_legend.config(text="16维策略: 冷热18+遗漏14+尾数12+跨度8+奇偶8+大小8+跟随8+重邻孤8(基础92) | 012路6+均值回归5+边码5+模式匹配6+动量4+遗漏回补5+周期4+黄金3(新增38) | 质数+AC+和值+位置+振幅+间隔+波动(加分~90) | 尾数"+str(w)+"种 跨度"+str(s)+" 重号"+str(r))
        except: pass
    def update_data_info(self):
        self.di.config(state=tk.NORMAL); self.di.delete(1.0,tk.END)
        from database import get_ssq_count,get_dlt_count
        s=get_ssq_count(); d=get_dlt_count()
        self.di.insert(tk.END,"SSQ:"+str(s)+"期 | DLT:"+str(d)+"期"); self.di.config(state=tk.DISABLED)
    def update_recent(self):
        self.rt.delete(1.0,tk.END)
        try:
            from database import get_all_ssq,get_all_dlt
            s=get_all_ssq(); d=get_all_dlt()
            text="SSQ:\n"
            for x in s[-5:]:
                text+="#"+str(x["period"])+": ["+str(x["red1"])+" "+str(x["red2"])+" "+str(x["red3"])+" "+str(x["red4"])+" "+str(x["red5"])+" "+str(x["red6"])+"] + ["+str(x["blue"])+"]\n"
            text+="\nDLT:\n"
            for x in d[-5:]:
                text+="#"+str(x["period"])+": ["+str(x["front1"])+" "+str(x["front2"])+" "+str(x["front3"])+" "+str(x["front4"])+" "+str(x["front5"])+"] + ["+str(x["back1"])+" "+str(x["back2"])+"]\n"
            self.rt.insert(tk.END,text)
        except: self.rt.insert(tk.END,"暂无数据")
