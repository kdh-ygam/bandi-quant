#!/usr/bin/env python3
"""
경매 투자 분석 툴 - 메인 실행 파일
파파의 경매 도우미 🏠

사용법:
    python main.py --help
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import check_config, DATA_DIR, LOG_DIR


def init_project():
    """프로젝트 초기화"""
    print("🚀 경매 분석 툴 초기화 중...")
    
    # 디렉토리 생성
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # 설정 확인
    check_config()
    
    print("✅ 초기화 완료!")


def run_scraper():
    """스크래퍼 실행"""
    print("🔍 경매 데이터 수집 시작...")
    # TODO: Phase 2에서 구현
    print("   (Phase 2에서 구현 예정)")


def run_analyzer():
    """AI 분석 실행"""
    print("🤖 AI 분석 시작...")
    # TODO: Phase 3에서 구현
    print("   (Phase 3에서 구현 예정)")


def run_calculator():
    """수익성 계산 실행"""
    print("🧮 수익성 계산 시작...")
    # TODO: Phase 4에서 구현
    print("   (Phase 4에서 구현 예정)")


def run_dashboard():
    """웹 대시보드 실행"""
    print("📊 대시보드 시작...")
    # TODO: Phase 5에서 구현
    print("   (Phase 5에서 구현 예정)")
    print("\n💡 실행: cd dashboard && streamlit run app.py")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="파파의 경매 투자 분석 툴",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py init           # 프로젝트 초기화
  python main.py scraper        # 데이터 수집
  python main.py analyzer       # AI 분석
  python main.py calculator     # 수익성 계산
  python main.py dashboard      # 대시보드 실행
        """
    )
    
    parser.add_argument(
        "command",
        choices=["init", "scraper", "analyzer", "calculator", "dashboard"],
        help="실행할 명령"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_project()
    elif args.command == "scraper":
        run_scraper()
    elif args.command == "analyzer":
        run_analyzer()
    elif args.command == "calculator":
        run_calculator()
    elif args.command == "dashboard":
        run_dashboard()


if __name__ == "__main__":
    main()
