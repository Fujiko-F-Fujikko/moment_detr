# run_tests.py

#!/usr/bin/env python3
"""
テスト実行スクリプト

このスクリプトは、pytestがインストールされていない環境でも
標準のunittestフレームワークを使用してテストを実行できます。
"""

import sys
import os
import unittest
import logging
from pathlib import Path

# テスト対象モジュールのインポートのためのパス設定
test_dir = Path(__file__).parent
refactor_dir = test_dir.parent
src_dir = refactor_dir / "src"
sys.path.insert(0, str(src_dir))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def discover_and_run_tests():
    """テストを発見して実行"""
    
    # QApplicationの初期化
    try:
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication([])
        logger.info("PyQt6 application initialized")
    except ImportError as e:
        logger.error(f"PyQt6 import failed: {e}")
        logger.error("Please install PyQt6: pip install PyQt6")
        return False
    
    # テストディスカバリー
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # テスト実行
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,  # テスト中の出力をキャプチャ
        stream=sys.stdout
    )
    
    logger.info(f"Running tests from {start_dir}")
    logger.info("=" * 70)
    
    result = runner.run(suite)
    
    # 結果のサマリー
    logger.info("=" * 70)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        logger.error("\nFAILURES:")
        for test, traceback in result.failures:
            logger.error(f"- {test}: {traceback}")
    
    if result.errors:
        logger.error("\nERRORS:")
        for test, traceback in result.errors:
            logger.error(f"- {test}: {traceback}")
    
    # 成功判定
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        logger.info("\nAll tests passed! ✅")
    else:
        logger.error(f"\nSome tests failed! ❌")
    
    return success


def run_specific_test(test_module_name):
    """特定のテストモジュールを実行"""
    
    logger.info(f"Running specific test: {test_module_name}")
    
    try:
        # QApplicationの初期化
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication([])
        
        # 特定のテストモジュールをインポート
        test_module = __import__(test_module_name)
        
        # テストスイートを作成
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # テスト実行
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except ImportError as e:
        logger.error(f"Failed to import test module {test_module_name}: {e}")
        return False


def check_dependencies():
    """依存関係をチェック"""
    dependencies = [
        ('PyQt6', 'PyQt6.QtWidgets'),
        ('PyQt6.QtCore', 'PyQt6.QtCore'),
        ('PyQt6.QtGui', 'PyQt6.QtGui'),
        ('PyQt6.QtMultimedia', 'PyQt6.QtMultimedia'),
        ('PyQt6.QtMultimediaWidgets', 'PyQt6.QtMultimediaWidgets'),
    ]
    
    missing_deps = []
    
    for name, module in dependencies:
        try:
            __import__(module)
            logger.info(f"✅ {name} is available")
        except ImportError:
            logger.error(f"❌ {name} is missing")
            missing_deps.append(name)
    
    if missing_deps:
        logger.error(f"\nMissing dependencies: {', '.join(missing_deps)}")
        logger.error("Install them with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for the refactored video annotation tool')
    parser.add_argument(
        '--test', '-t',
        help='Run specific test module (e.g., test_annotation_data_manager)'
    )
    parser.add_argument(
        '--check-deps', '-c',
        action='store_true',
        help='Check dependencies only'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 依存関係チェック
    if args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # 特定のテスト実行
    if args.test:
        success = run_specific_test(args.test)
    else:
        # 全テスト実行
        success = discover_and_run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
