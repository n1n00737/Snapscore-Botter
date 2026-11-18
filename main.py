"""
Snap Automation Engine Pro (SAE-Pro)
Author: n1n00737
Version: 1.3.0
Description: High-performance, anti-detection macro automation engine for Snapchat Web.
"""

import json
import os
import platform
import random
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional, Tuple

try:
    import colorama
    from colorama import Fore, Style, init
    import keyboard
    import pyautogui
except ImportError as err:
    print(f"[!] Missing required dependency: {err}")
    print("[*] Please run 'Install_Requirements.bat' or 'pip install -r requirements.txt'")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Initialize colorama for ANSI terminal formatting
init(autoreset=True)

# Safety: moving mouse cursor to screen corner instantly triggers FailSafeException
pyautogui.FAILSAFE = True

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
APP_VERSION = "1.3.0"
AUTHOR = "n1n00737"


@dataclass
class AppConfig:
    # Delays & Throttle parameters
    loop_delay: float = 4.5
    click_delay: float = 0.9
    position_delay: float = 0.4
    shortcut_users: int = 50

    # Anti-Detection & Humanization Heuristics
    human_mode: bool = True
    random_jitter: int = 3
    auto_break_enabled: bool = True
    break_interval: int = 30
    break_duration: float = 12.0
    sound_effects: bool = True

    # Saved Coordinates (x, y)
    camera_pos: Optional[Tuple[int, int]] = None
    send_to_pos: Optional[Tuple[int, int]] = None
    shortcut_pos: Optional[Tuple[int, int]] = None
    select_all_pos: Optional[Tuple[int, int]] = None

    # Persistent Lifetime Telemetry
    lifetime_snaps: int = 0
    lifetime_cycles: int = 0
    lifetime_seconds: float = 0.0

    @classmethod
    def load(cls) -> "AppConfig":
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                return cls()
        return cls()

    def save(self) -> None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to save configuration: {e}")


def play_sound(sound_type: str, cfg: AppConfig) -> None:
    if not cfg.sound_effects or platform.system() != "Windows":
        return
    try:
        import winsound

        tones = {
            "capture": [(1200, 90)],
            "start": [(880, 100), (1174, 140)],
            "pause": [(650, 150)],
            "resume": [(1100, 150)],
            "stop": [(550, 200)],
            "break": [(800, 80), (950, 120)],
        }
        for freq, duration in tones.get(sound_type, []):
            winsound.Beep(freq, duration)
    except Exception:
        pass


def set_terminal_title(text: str) -> None:
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleTitleW(text)
        except Exception:
            pass
    else:
        sys.stdout.write(f"\33]0;{text}\a")
        sys.stdout.flush()


def clear_screen() -> None:
    os.system("cls" if platform.system() == "Windows" else "clear")


def get_display_resolution() -> str:
    try:
        w, h = pyautogui.size()
        return f"{w}x{h}"
    except Exception:
        return "Unknown"


def print_banner() -> None:
    clear_screen()
    banner = f"""{Fore.CYAN}
  ███████╗███╗   ██╗ █████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██████╗ 
  ██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔══██╗
  ███████╗██╔██╗ ██║███████║██████╔╝███████╗██╔██╗ ██║███████║██████╔╝
  ╚════██║██║╚██╗██║██╔══██║██╔═══╝ ╚════██║██║╚██╗██║██╔══██║██╔═══╝ 
  ███████║██║ ╚████║██║  ██║██║     ███████║██║ ╚████║██║  ██║██║     
  ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     {Style.RESET_ALL}
  {Fore.WHITE}Snap Automation Engine Pro {Fore.CYAN}v{APP_VERSION}{Fore.WHITE} | Author: {Fore.LIGHTMAGENTA_EX}{AUTHOR}{Fore.WHITE} | Display: {Fore.LIGHTCYAN_EX}{get_display_resolution()}
  {Fore.BLACK + Style.BRIGHT}────────────────────────────────────────────────────────────────────────────
"""
    print(banner)


def log_info(msg: str) -> None:
    print(f"  {Fore.CYAN}[*]{Fore.WHITE} {msg}")


def log_success(msg: str) -> None:
    print(f"  {Fore.GREEN}[+]{Fore.WHITE} {msg}")


def log_warn(msg: str) -> None:
    print(f"  {Fore.YELLOW}[!]{Fore.WHITE} {msg}")


def log_step(step: str, desc: str) -> None:
    print(f"  {Fore.CYAN}[{step}]{Fore.WHITE} {desc}")


def format_elapsed(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}h {mins:02d}m {secs:02d}s"
    return f"{mins:02d}m {secs:02d}s"


class SnapAutomation:
    def __init__(self, config: AppConfig):
        self.cfg = config
        self.session_cycles = 0
        self.session_snaps = 0
        self.first_cycle = True
        self.is_paused = False

    def is_calibrated(self) -> bool:
        return bool(
            self.cfg.camera_pos
            and self.cfg.send_to_pos
            and self.cfg.shortcut_pos
            and self.cfg.select_all_pos
        )

    def calibrate(self) -> None:
        print_banner()
        print(f"  {Fore.LIGHTCYAN_EX}CALIBRATION WIZARD{Style.RESET_ALL}\n")
        log_info("Please position your Snapchat Web browser prominently on screen.")
        log_info("Hover your mouse cursor over each UI target, then press [F] to capture.\n")

        steps = [
            ("camera_pos", "Camera button (Take Snap button)"),
            ("send_to_pos", "'Send To' action button"),
            ("shortcut_pos", "Your Shortcut group tab/button"),
            ("select_all_pos", "'Select All' checkbox inside shortcut list"),
        ]

        for attr, label in steps:
            log_step("TARGET", f"Hover over {Fore.YELLOW}{label}{Fore.WHITE}, then press {Fore.GREEN}[F]")
            while True:
                if keyboard.is_pressed("f"):
                    pos = pyautogui.position()
                    setattr(self.cfg, attr, (pos.x, pos.y))
                    play_sound("capture", self.cfg)
                    log_success(f"Registered: {Fore.GREEN}({pos.x}, {pos.y}){Fore.WHITE}\n")
                    time.sleep(self.cfg.position_delay)
                    break
                time.sleep(0.04)

        self.cfg.save()
        log_success("All coordinates calibrated and committed to config.json!\n")
        time.sleep(0.4)

    def verify_preview(self) -> None:
        print_banner()
        print(f"  {Fore.LIGHTCYAN_EX}COORDINATE VERIFICATION PREVIEW{Style.RESET_ALL}\n")
        if not self.is_calibrated():
            log_warn("Engine is not calibrated yet. Run Calibration first.")
            input("\n  Press Enter to return...")
            return

        log_info("The cursor will smoothly travel across each recorded coordinate.")
        log_info("Verify that the crosshair aligns with the respective buttons.")
        log_warn("Press [Q] or [ESC] at any time to cancel.\n")
        input("  Press Enter to begin inspection...")

        targets = [
            ("Camera Button", self.cfg.camera_pos),
            ("Send To Button", self.cfg.send_to_pos),
            ("Shortcut Group", self.cfg.shortcut_pos),
            ("Select All Checkbox", self.cfg.select_all_pos),
        ]

        time.sleep(0.5)
        for label, pos in targets:
            if keyboard.is_pressed("q") or keyboard.is_pressed("esc"):
                log_warn("Verification aborted by user.")
                break
            log_step("CHECK", f"Inspecting {Fore.YELLOW}{label}{Fore.WHITE} -> {pos}")
            pyautogui.moveTo(pos[0], pos[1], duration=0.35, tween=pyautogui.easeInOutQuad)
            time.sleep(1.5)

        log_success("Inspection completed successfully.\n")
        input("  Press Enter to return to main menu...")

    def human_click(self, target: Tuple[int, int], wait_before: float = 0.0) -> None:
        if wait_before > 0:
            time.sleep(wait_before)

        x, y = target
        if self.cfg.human_mode:
            # Subtle random jitter
            jit_x = random.randint(-self.cfg.random_jitter, self.cfg.random_jitter)
            jit_y = random.randint(-self.cfg.random_jitter, self.cfg.random_jitter)
            tx, ty = x + jit_x, y + jit_y

            # Smooth ease-in-out cursor interpolation
            duration = random.uniform(0.14, 0.26)
            pyautogui.moveTo(tx, ty, duration=duration, tween=pyautogui.easeInOutQuad)
            time.sleep(random.uniform(0.04, 0.08))
        else:
            pyautogui.moveTo(x, y)
            time.sleep(0.02)

        pyautogui.click()

    def run(self) -> None:
        if not self.is_calibrated():
            log_warn("Missing calibration profile. Starting Calibration Wizard...")
            time.sleep(1)
            self.calibrate()

        print_banner()
        mode_str = f"{Fore.GREEN}ON (Bézier + Jitter)" if self.cfg.human_mode else f"{Fore.YELLOW}OFF (Instant)"
        break_str = f"{Fore.GREEN}Every {self.cfg.break_interval} cycles ({self.cfg.break_duration}s)" if self.cfg.auto_break_enabled else f"{Fore.YELLOW}Disabled"

        log_info(f"Target Shortcut Members : {Fore.YELLOW}{self.cfg.shortcut_users}")
        log_info(f"Cycle Delay / Pacing    : {Fore.YELLOW}{self.cfg.loop_delay}s{Fore.WHITE} (± variance)")
        log_info(f"Action Speed (Click)    : {Fore.YELLOW}{self.cfg.click_delay}s")
        log_info(f"Anti-Detection Humanizer: {mode_str}")
        log_info(f"Anti-Flood Auto-Breaks  : {break_str}")
        print()
        log_info(f"Hotkeys: {Fore.GREEN}[F]{Fore.WHITE} Start | {Fore.YELLOW}[P]{Fore.WHITE} Pause/Resume | {Fore.RED}[Q/ESC]{Fore.WHITE} Stop")
        log_warn("Failsafe: You can also instantly kill the bot by flicking your mouse to any screen corner.\n")
        print(f"  {Fore.CYAN}Focus your Snapchat window and press {Fore.GREEN}[F]{Fore.CYAN} to engage...{Style.RESET_ALL}")

        while True:
            if keyboard.is_pressed("f"):
                break
            time.sleep(0.04)

        play_sound("start", self.cfg)
        time.sleep(0.5)

        start_time = time.time()
        self.session_cycles = 0
        self.session_snaps = 0
        self.first_cycle = True
        self.is_paused = False

        try:
            while True:
                # Handle Quit
                if keyboard.is_pressed("q") or keyboard.is_pressed("esc"):
                    play_sound("stop", self.cfg)
                    log_warn("Stop signal caught from user.")
                    break

                # Handle Pause / Resume toggle
                if keyboard.is_pressed("p"):
                    self.is_paused = not self.is_paused
                    if self.is_paused:
                        play_sound("pause", self.cfg)
                        set_terminal_title(f"PAUSED - Snap Automation Engine | {AUTHOR}")
                        print(f"\n  {Fore.YELLOW}⏸ ENGINE PAUSED{Fore.WHITE} - Press {Fore.GREEN}[P]{Fore.WHITE} to resume or {Fore.RED}[Q]{Fore.WHITE} to stop.")
                    else:
                        play_sound("resume", self.cfg)
                        print(f"  {Fore.GREEN}▶ ENGINE RESUMED{Style.RESET_ALL}\n")
                    time.sleep(0.4)

                if self.is_paused:
                    time.sleep(0.1)
                    continue

                # Execute an automated dispatch cycle
                self.execute_cycle()
                self.session_cycles += 1
                self.session_snaps = self.session_cycles * self.cfg.shortcut_users

                elapsed = time.time() - start_time
                velocity = (self.session_snaps / elapsed * 60) if elapsed > 0 else 0

                set_terminal_title(
                    f"Active | Snaps: {self.session_snaps:,} | Rate: ~{velocity:,.0f}/min | {format_elapsed(elapsed)} | {AUTHOR}"
                )

                print_banner()
                print(f"  {Fore.GREEN}● ENGINE ACTIVE{Style.RESET_ALL}  (Hotkeys: {Fore.YELLOW}[P]{Fore.WHITE} Pause | {Fore.RED}[Q]{Fore.WHITE} Stop)\n")
                print(f"  {Fore.WHITE}Session Runtime   : {Fore.CYAN}{format_elapsed(elapsed)}")
                print(f"  {Fore.WHITE}Cycles Executed   : {Fore.CYAN}{self.session_cycles:,}")
                print(f"  {Fore.WHITE}Snaps Delivered   : {Fore.GREEN}{self.session_snaps:,}")
                print(f"  {Fore.WHITE}Delivery Velocity : {Fore.LIGHTMAGENTA_EX}~{velocity:,.0f} snaps/min")
                print(f"  {Fore.WHITE}Lifetime Total    : {Fore.LIGHTCYAN_EX}{self.cfg.lifetime_snaps + self.session_snaps:,} snaps")

                # Anti-flood Auto-Break feature
                if (
                    self.cfg.auto_break_enabled
                    and self.session_cycles > 0
                    and self.session_cycles % self.cfg.break_interval == 0
                ):
                    play_sound("break", self.cfg)
                    print(f"\n  {Fore.LIGHTMAGENTA_EX}☕ Scheduled Cool-Down Breath ({self.cfg.break_duration}s)... Anti-ban pacing protection.")
                    break_end = time.time() + self.cfg.break_duration
                    while time.time() < break_end:
                        if keyboard.is_pressed("q") or keyboard.is_pressed("esc"):
                            break
                        rem = max(0, int(break_end - time.time()))
                        sys.stdout.write(f"\r  {Fore.CYAN}[Cooling Down]{Fore.WHITE} Resuming in {rem:02d}s... [Q to cancel]   ")
                        sys.stdout.flush()
                        time.sleep(0.2)
                    print()

                # Dynamic sleep interval with randomized timing variance
                variance = random.uniform(0.92, 1.12) if self.cfg.human_mode else 1.0
                target_sleep = self.cfg.loop_delay * variance
                sleep_end = time.time() + target_sleep

                while time.time() < sleep_end:
                    if keyboard.is_pressed("q") or keyboard.is_pressed("esc"):
                        break
                    if keyboard.is_pressed("p"):
                        break
                    remaining = max(0.0, sleep_end - time.time())
                    sys.stdout.write(
                        f"\r  {Fore.BLACK + Style.BRIGHT}Next payload dispatch in: {remaining:03.1f}s... [P: Pause | Q: Exit]   "
                    )
                    sys.stdout.flush()
                    time.sleep(0.08)

                sys.stdout.write("\r" + " " * 75 + "\r")
                sys.stdout.flush()

        except pyautogui.FailSafeException:
            log_warn("PyAutoGUI FailSafe triggered: Cursor flicked to corner. Engine halted safely.")
        except KeyboardInterrupt:
            log_warn("Process manually interrupted by user.")

        session_duration = time.time() - start_time

        # Update persistent lifetime metrics
        self.cfg.lifetime_snaps += self.session_snaps
        self.cfg.lifetime_cycles += self.session_cycles
        self.cfg.lifetime_seconds += session_duration
        self.cfg.save()

        print_banner()
        print(f"  {Fore.CYAN}SESSION SUMMARY & TELEMETRY{Style.RESET_ALL}\n")
        print(f"  {Fore.WHITE}Snaps Delivered This Session : {Fore.GREEN}{self.session_snaps:,}")
        print(f"  {Fore.WHITE}Cycles Executed              : {Fore.CYAN}{self.session_cycles:,}")
        print(f"  {Fore.WHITE}Session Duration             : {Fore.CYAN}{format_elapsed(session_duration)}")
        print(f"  {Fore.WHITE}All-Time Lifetime Snaps      : {Fore.LIGHTMAGENTA_EX}{self.cfg.lifetime_snaps:,}")
        print(f"  {Fore.WHITE}All-Time Total Runtime       : {Fore.LIGHTMAGENTA_EX}{format_elapsed(self.cfg.lifetime_seconds)}")
        input(f"\n  {Fore.WHITE}Press Enter to return to main menu...")

    def execute_cycle(self) -> None:
        cd = self.cfg.click_delay
        if self.cfg.human_mode:
            cd = cd * random.uniform(0.94, 1.08)

        # 1. Switch / Activate camera mode
        if self.first_cycle:
            self.human_click(self.cfg.camera_pos)
            self.first_cycle = False
            time.sleep(cd)

        # 2. Shutter click (Capture snap)
        self.human_click(self.cfg.camera_pos)
        time.sleep(cd)

        # 3. Open recipient selection panel
        self.human_click(self.cfg.send_to_pos)
        time.sleep(cd)

        # 4. Activate target shortcut group
        self.human_click(self.cfg.shortcut_pos)
        time.sleep(cd)

        # 5. Check 'Select All'
        self.human_click(self.cfg.select_all_pos)
        time.sleep(cd)

        # 6. Dispatch payload
        self.human_click(self.cfg.send_to_pos)


def configure_settings(cfg: AppConfig) -> None:
    while True:
        print_banner()
        mode_str = f"{Fore.GREEN}Enabled" if cfg.human_mode else f"{Fore.RED}Disabled"
        break_str = f"{Fore.GREEN}Enabled ({cfg.break_interval} cyc / {cfg.break_duration}s)" if cfg.auto_break_enabled else f"{Fore.RED}Disabled"
        sound_str = f"{Fore.GREEN}Enabled" if cfg.sound_effects else f"{Fore.RED}Muted"

        print(f"  {Fore.LIGHTCYAN_EX}ENGINE PARAMETERS & PREFERENCES{Style.RESET_ALL}\n")
        print(f"  {Fore.CYAN}[1]{Fore.WHITE} Shortcut Recipient Count   : {Fore.YELLOW}{cfg.shortcut_users} members")
        print(f"  {Fore.CYAN}[2]{Fore.WHITE} Loop Delay (Throttle)      : {Fore.YELLOW}{cfg.loop_delay}s")
        print(f"  {Fore.CYAN}[3]{Fore.WHITE} Action Click Delay         : {Fore.YELLOW}{cfg.click_delay}s")
        print(f"  {Fore.CYAN}[4]{Fore.WHITE} Anti-Detection Human Mode  : {mode_str}")
        print(f"  {Fore.CYAN}[5]{Fore.WHITE} Anti-Flood Cool-Down Breaks: {break_str}")
        print(f"  {Fore.CYAN}[6]{Fore.WHITE} Audio Cues (Beeps)         : {sound_str}")
        print(f"  {Fore.CYAN}[7]{Fore.WHITE} Reset Lifetime Statistics")
        print(f"  {Fore.CYAN}[0]{Fore.WHITE} Back to Main Menu\n")

        choice = input(f"  {Fore.CYAN}Select an option > {Style.RESET_ALL}").strip()

        if choice == "1":
            try:
                val = int(input(f"  {Fore.WHITE}Enter recipient count: {Fore.YELLOW}"))
                if val > 0:
                    cfg.shortcut_users = val
                    cfg.save()
                    log_success("Saved.")
            except ValueError:
                pass
        elif choice == "2":
            try:
                val = float(input(f"  {Fore.WHITE}Enter loop interval in seconds (default 4.5): {Fore.YELLOW}"))
                if val >= 0.5:
                    cfg.loop_delay = val
                    cfg.save()
                    log_success("Saved.")
            except ValueError:
                pass
        elif choice == "3":
            try:
                val = float(input(f"  {Fore.WHITE}Enter click delay in seconds (default 0.9): {Fore.YELLOW}"))
                if val >= 0.2:
                    cfg.click_delay = val
                    cfg.save()
                    log_success("Saved.")
            except ValueError:
                pass
        elif choice == "4":
            cfg.human_mode = not cfg.human_mode
            cfg.save()
            log_success(f"Human Mode is now {'Enabled' if cfg.human_mode else 'Disabled'}.")
            time.sleep(0.4)
        elif choice == "5":
            cfg.auto_break_enabled = not cfg.auto_break_enabled
            cfg.save()
            log_success(f"Cool-Down Breaks are now {'Enabled' if cfg.auto_break_enabled else 'Disabled'}.")
            time.sleep(0.4)
        elif choice == "6":
            cfg.sound_effects = not cfg.sound_effects
            cfg.save()
            log_success(f"Sound Effects are now {'Enabled' if cfg.sound_effects else 'Muted'}.")
            time.sleep(0.4)
        elif choice == "7":
            confirm = input(f"  {Fore.RED}Reset all lifetime stats to 0? (y/N): {Style.RESET_ALL}").lower()
            if confirm == "y":
                cfg.lifetime_snaps = 0
                cfg.lifetime_cycles = 0
                cfg.lifetime_seconds = 0.0
                cfg.save()
                log_success("Lifetime statistics cleared.")
                time.sleep(0.5)
        elif choice == "0":
            break


def show_guide() -> None:
    print_banner()
    print(f"  {Fore.LIGHTCYAN_EX}SYSTEM ARCHITECTURE & OPERATIONAL GUIDE{Style.RESET_ALL}\n")
    print(f"  {Fore.CYAN}1.{Fore.WHITE} {Fore.YELLOW}Web Client Preparation:{Fore.WHITE}")
    print("     Log in to web.snapchat.com on your desktop browser.")
    print("     Permit camera/microphone access. (OBS Virtual Camera can be used if no physical cam is plugged in).\n")
    print(f"  {Fore.CYAN}2.{Fore.WHITE} {Fore.YELLOW}Shortcut Setup:{Fore.WHITE}")
    print("     From your Snapchat mobile app, construct a shortcut including your target audience.\n")
    print(f"  {Fore.CYAN}3.{Fore.WHITE} {Fore.YELLOW}Coordinate Calibration:{Fore.WHITE}")
    print("     Teach the engine the precise button coordinates on your monitor once.")
    print("     Coordinates are serialized directly into config.json for zero-friction future startups.\n")
    print(f"  {Fore.CYAN}4.{Fore.WHITE} {Fore.YELLOW}Anti-Detection Safeguards:{Fore.WHITE}")
    print("     - Human Mode activates Bézier curved paths and ±3px jitter to counter bot heuristics.")
    print("     - Anti-Flood cool-downs emulate realistic user pauses.\n")
    print(f"  {Fore.CYAN}5.{Fore.WHITE} {Fore.YELLOW}Live Control Keys:{Fore.WHITE}")
    print(f"     - {Fore.GREEN}[F]{Fore.WHITE}       Engage execution loop")
    print(f"     - {Fore.YELLOW}[P]{Fore.WHITE}       Pause / Unpause engine without terminating")
    print(f"     - {Fore.RED}[Q / ESC]{Fore.WHITE} Terminate cleanly and persist session metrics")
    print(f"     - {Fore.RED}Corner{Fore.WHITE}   Instant hardware failsafe (move cursor to screen corner)\n")
    input(f"  {Fore.WHITE}Press Enter to return to main menu...")


def main() -> None:
    cfg = AppConfig.load()
    set_terminal_title(f"Snap Automation Engine Pro v{APP_VERSION} | {AUTHOR}")

    while True:
        print_banner()
        calibrated_str = f"{Fore.GREEN}Ready (Saved)" if cfg.camera_pos else f"{Fore.YELLOW}Uncalibrated"
        print(f"  Calibration Profile : {calibrated_str}{Style.RESET_ALL}")
        print(f"  All-Time Snaps Sent : {Fore.LIGHTMAGENTA_EX}{cfg.lifetime_snaps:,}{Style.RESET_ALL}\n")
        print(f"  {Fore.CYAN}[1]{Fore.WHITE} Launch Automation Engine")
        print(f"  {Fore.CYAN}[2]{Fore.WHITE} Calibrate Screen Coordinates")
        print(f"  {Fore.CYAN}[3]{Fore.WHITE} Verify & Preview Coordinates")
        print(f"  {Fore.CYAN}[4]{Fore.WHITE} Engine Parameters & Preferences")
        print(f"  {Fore.CYAN}[5]{Fore.WHITE} System Guide & Architecture")
        print(f"  {Fore.CYAN}[0]{Fore.WHITE} Exit\n")

        choice = input(f"  {Fore.CYAN}Select an option > {Style.RESET_ALL}").strip()
        bot = SnapAutomation(cfg)

        if choice == "1":
            bot.run()
        elif choice == "2":
            bot.calibrate()
        elif choice == "3":
            bot.verify_preview()
        elif choice == "4":
            configure_settings(cfg)
        elif choice == "5":
            show_guide()
        elif choice == "0":
            clear_screen()
            print(f"\n  {Fore.CYAN}Engine shut down cleanly. Developed by {AUTHOR}.\n")
            break


if __name__ == "__main__":
    main()
