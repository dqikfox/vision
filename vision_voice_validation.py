"""Real-time voice recognition validation for Vision production readiness.

This script performs live microphone testing and voice command recognition validation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import sounddevice as sd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("vision_voice_validation.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VoiceValidation:
    """Voice hardware and recognition validation."""

    def __init__(self):
        self.results = {}

    async def test_audio_devices(self):
        """Enumerate and validate audio input devices."""
        logger.info("\n" + "=" * 80)
        logger.info("AUDIO DEVICE VALIDATION")
        logger.info("=" * 80)

        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]

            logger.info(f"Total audio devices found: {len(devices)}")
            logger.info(f"Input devices (microphones): {len(input_devices)}")

            if not input_devices:
                logger.error("[ FAIL ] No microphone devices found!")
                self.results['audio_devices'] = False
                return False

            logger.info("\nMicrophone devices:")
            for idx, dev in enumerate(input_devices):
                logger.info(f"  [{idx}] {dev['name']}")
                logger.info(f"      Channels: {dev['max_input_channels']}")
                logger.info(f"      Sample Rate: {dev['default_samplerate']} Hz")

            self.results['audio_devices'] = True
            self.results['input_device_count'] = len(input_devices)
            self.results['default_device'] = sd.query_devices(kind='input')['name']

            logger.info("\n[ PASS ] Audio validation complete")
            logger.info(f"Default input device: {self.results['default_device']}")
            return True

        except Exception as e:
            logger.error(f"[ FAIL ] Audio device validation failed: {e}")
            self.results['audio_devices'] = False
            return False

    async def test_microphone_levels(self, duration_seconds=3):
        """Test microphone input levels (no actual recording)."""
        logger.info("\n" + "=" * 80)
        logger.info("MICROPHONE LEVEL TEST")
        logger.info("=" * 80)

        try:
            logger.info(f"Monitoring microphone levels for {duration_seconds} seconds...")
            logger.info("Speak into your microphone to test audio capture...")

            # Callback to measure audio levels
            max_level = 0
            sample_count = 0

            def audio_callback(indata, frames, time_info, status):
                nonlocal max_level, sample_count
                if status:
                    logger.warning(f"Audio callback status: {status}")

                volume_norm = np.abs(indata).mean()
                if volume_norm > max_level:
                    max_level = volume_norm
                sample_count += frames

            import numpy as np

            # Record for specified duration
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000):
                await asyncio.sleep(duration_seconds)

            logger.info(f"\nRecorded {sample_count} samples")
            logger.info(f"Maximum audio level detected: {max_level:.6f}")

            if max_level < 0.001:
                logger.warning("[ WARN ] Very low audio levels detected - check microphone connection")
                self.results['mic_levels'] = 'low'
            elif max_level > 0.01:
                logger.info("[ PASS ] Strong audio signal detected")
                self.results['mic_levels'] = 'good'
            else:
                logger.info("[ PASS ] Audio signal detected (moderate)")
                self.results['mic_levels'] = 'moderate'

            self.results['max_audio_level'] = float(max_level)
            return True

        except Exception as e:
            logger.error(f"[ FAIL ] Microphone level test failed: {e}")
            self.results['mic_levels'] = 'failed'
            return False

    async def test_voice_command_parser(self):
        """Test voice command parsing with real phrases."""
        logger.info("\n" + "=" * 80)
        logger.info("VOICE COMMAND PARSER VALIDATION")
        logger.info("=" * 80)

        try:
            from vision_voice_commands import get_voice_parser

            parser = get_voice_parser()

            # Real-world test phrases a hands-free user might say
            test_phrases = [
                ("open chrome", "open_application"),
                ("click the start button", "click"),
                ("type hello world", "type_text"),
                ("scroll down the page", "scroll_down"),
                ("maximize this window", "maximize_window"),
                ("turn up the volume", "volume_up"),
                ("what's on my screen", "read_screen"),
                ("close this tab", "close_tab"),
                ("switch to next window", "switch_window"),
                ("search for python tutorial", "web_search"),
                ("take a screenshot", "screenshot"),
                ("play my music", "media_play"),
                ("help me", "help"),
                ("save this file", "save_file"),
                ("copy that", "copy")
            ]

            passed = 0
            failed = 0

            for phrase, expected_cmd in test_phrases:
                result = parser.parse(phrase)
                if result and result.get("command") == expected_cmd:
                    logger.info(f"  [ OK ] '{phrase}' → {expected_cmd}")
                    passed += 1
                else:
                    got = result.get("command") if result else "None"
                    logger.error(f"  [ FAIL ] '{phrase}' expected {expected_cmd}, got {got}")
                    failed += 1

            success_rate = passed / len(test_phrases) * 100
            logger.info(f"\nRecognition rate: {success_rate:.1f}% ({passed}/{len(test_phrases)} passed)")

            self.results['voice_parser'] = {
                'total': len(test_phrases),
                'passed': passed,
                'failed': failed,
                'success_rate': success_rate
            }

            if success_rate >= 80:
                logger.info("[ PASS ] Voice command parser validation complete")
                return True
            else:
                logger.error("[ FAIL ] Voice parser below 80% threshold")
                return False

        except Exception as e:
            logger.error(f"[ FAIL ] Voice parser test failed: {e}")
            self.results['voice_parser'] = {'error': str(e)}
            return False

    async def generate_report(self):
        """Generate voice validation report."""
        logger.info("\n" + "=" * 80)
        logger.info("VOICE VALIDATION SUMMARY")
        logger.info("=" * 80)

        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": self.results,
            "overall_status": "PASS" if all(
                v for k, v in self.results.items()
                if isinstance(v, bool)
            ) else "PARTIAL"
        }

        # Save report
        report_path = Path("vision_voice_validation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\nReport saved to: {report_path}")
        logger.info(f"Overall status: {report['overall_status']}")

        return report

    async def run_all_tests(self):
        """Run complete voice validation suite."""
        logger.info("\n" + "=" * 80)
        logger.info("VISION VOICE VALIDATION SUITE")
        logger.info("=" * 80)
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run tests
        await self.test_audio_devices()
        await self.test_voice_command_parser()

        # Only test mic levels if audio devices present
        if self.results.get('audio_devices'):
            logger.info("\n⚠️  Microphone level test will run for 3 seconds...")
            logger.info("⚠️  Please speak into your microphone to test audio capture!")
            logger.info("⚠️  This is automated - no user interaction needed after this.\n")
            await asyncio.sleep(1)  # Brief pause
            await self.test_microphone_levels()

        # Generate report
        report = await self.generate_report()

        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 80)

        return report


async def main():
    """Main validation entry point."""
    validator = VoiceValidation()
    report = await validator.run_all_tests()

    # Print final summary
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "VOICE VALIDATION RESULTS" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")

    print(f"\nAudio Devices: {'✓ PASS' if report['validation_results'].get('audio_devices') else '✗ FAIL'}")

    parser_results = report['validation_results'].get('voice_parser', {})
    if isinstance(parser_results, dict) and 'success_rate' in parser_results:
        success_rate = parser_results['success_rate']
        status = "✓ PASS" if success_rate >= 80 else "✗ FAIL"
        print(f"Voice Parser: {status} ({success_rate:.1f}% success rate)")

    mic_level = report['validation_results'].get('mic_levels', 'not_tested')
    print(f"Microphone Levels: {mic_level}")

    print(f"\nOverall Status: {report['overall_status']}")
    print("\nFull report: vision_voice_validation_report.json")
    print("Full logs: vision_voice_validation.log")


if __name__ == "__main__":
    asyncio.run(main())
