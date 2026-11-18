"""Assign YouTube publish slots (run before every scheduling session). Since 2026-11-18 this re-orders ALL unpublished Shorts,
scheduled ones included (SY: "잘 나온 컨텐츠 위주로 순서 다 바꿔줘"): see yt_reshuffle.py. Old pending-only planner: yt_plan_old.py."""
import runpy; runpy.run_path('yt_reshuffle.py', run_name='__main__')
