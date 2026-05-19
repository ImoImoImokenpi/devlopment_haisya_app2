document.addEventListener('DOMContentLoaded', function () {

    // room_detail.html: 車出しチェックボックスで座席数入力を表示/非表示
    const carCheck = document.getElementById('hasCarCheck');
    const capacityDiv = document.getElementById('capacityInput');
    if (carCheck && capacityDiv) {
        carCheck.addEventListener('change', function () {
            capacityDiv.classList.toggle('d-none', !this.checked);
        });
    }

    // create_room.html: 出演順チェックで部数設定を表示/非表示
    const scheduleCheck = document.getElementById('q_schedule');
    const settingDiv = document.getElementById('section_setting');
    if (scheduleCheck && settingDiv) {
        scheduleCheck.addEventListener('change', function () {
            settingDiv.classList.toggle('d-none', !this.checked);
        });
    }

    // profile_setting.html: アイコン画像プレビュー
    const iconInput = document.getElementById('iconInput');
    if (iconInput) {
        iconInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = e => {
                document.getElementById('iconPreview').src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    // join_code.html: 招待コード入力を大文字英数字のみに制限
    const joinCodeInput = document.getElementById('joinCodeInput');
    if (joinCodeInput) {
        joinCodeInput.addEventListener('input', function () {
            this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        });
    }

    // group_detail.html: 招待コードをクリップボードにコピー
    const copyBtn = document.querySelector('[data-invite-code]');
    if (copyBtn) {
        copyBtn.addEventListener('click', function () {
            navigator.clipboard.writeText(this.dataset.inviteCode);
            const toast = document.getElementById('copyToast');
            toast.classList.remove('d-none');
            setTimeout(() => toast.classList.add('d-none'), 1800);
        });
    }
});
