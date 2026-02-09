import subprocess
import sys
import os

def run_git_command(command):
    """Menjalankan perintah git dan menangani error jika ada."""
    try:
        # Menjalankan perintah di terminal
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            shell=True
        )
        # Jika berhasil, print outputnya
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        # Jika error (misal conflict atau tidak ada perubahan)
        print(f"❌ Error saat menjalankan: '{command}'")
        print(f"   Detail: {e.stderr.strip()}")
        sys.exit(1)

def git_push_automator():
    print("="*40)
    print("🚀 GITHUB PUSH AUTOMATOR")
    print("="*40)

    # 0. Cek apakah ini repository git
    if not os.path.exists(".git"):
        print("❌ Error: Folder ini bukan repository Git. Jalankan 'git init' terlebih dahulu.")
        return

    # 1. Input Pesan Commit
    commit_msg = input("📝 Masukkan Pesan Commit: ").strip()
    if not commit_msg:
        print("⚠️ Pesan commit tidak boleh kosong!")
        return

    # 2. Input Nama Branch (Default: main)
    branch_name = input("fY🌿 Masukkan Nama Branch (Enter untuk default 'main'): ").strip()
    if not branch_name:
        branch_name = "main"

    print("\n⏳ Memulai proses...")

    # 3. Eksekusi Perintah Git
    # git add .
    print("1️⃣  Menambahkan file (git add .)...")
    run_git_command("git add .")

    # git commit -m "pesan"
    print(f"2️⃣  Melakukan commit: '{commit_msg}'...")
    # Menggunakan try-except khusus di sini karena jika tidak ada perubahan, git commit akan return non-zero exit code
    try:
        subprocess.run(f'git commit -m "{commit_msg}"', check=True, shell=True, text=True, capture_output=True)
        print("   ✅ Commit berhasil.")
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stdout:
            print("   ⚠️ Tidak ada perubahan baru untuk di-commit.")
        else:
            print(f"   ❌ Error commit: {e.stderr}")
            return

    # git push
    print(f"3️⃣  Melakukan push ke origin/{branch_name}...")
    run_git_command(f"git push origin {branch_name}")

    print("\n🎉 SUKSES! Kode berhasil di-push ke GitHub.")
    print("="*40)

if __name__ == "__main__":
    git_push_automator()