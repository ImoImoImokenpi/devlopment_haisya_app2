const HOLIDAYS = {
    "2026-01-01":"元日","2026-01-12":"成人の日","2026-02-11":"建国記念の日",
    "2026-02-23":"天皇誕生日","2026-03-20":"春分の日","2026-04-29":"昭和の日",
    "2026-05-03":"憲法記念日","2026-05-04":"みどりの日","2026-05-05":"こどもの日",
    "2026-07-20":"海の日","2026-08-11":"山の日","2026-09-21":"敬老の日",
    "2026-09-23":"秋分の日","2026-10-12":"スポーツの日","2026-11-03":"文化の日",
    "2026-11-23":"勤労感謝の日"
};

document.addEventListener('DOMContentLoaded', function () {

    // home.html: FullCalendar
    const calendarEl = document.getElementById('calendar');
    if (calendarEl && typeof FullCalendar !== 'undefined') {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'ja',
            height: 'auto',
            eventDisplay: 'block',
            headerToolbar: { left: 'prev', center: 'title', right: 'next' },
            displayEventTime: false,
            dayCellContent: function(arg) {
                return { html: `<span>${arg.date.getDate()}</span>` };
            },
            dayCellDidMount: function(arg) {
                const d = arg.date.toISOString().split('T')[0];
                if (HOLIDAYS[d]) {
                    arg.el.classList.add('fc-day-holiday');
                    const num = arg.el.querySelector('.fc-daygrid-day-number');
                    if (num) num.title = HOLIDAYS[d];
                }
            },
            events: '/events/api/events',
            dateClick: function(info) {
                window.location.href = `/events/create?date=${info.dateStr}`;
            },
            eventClick: function(info) {
                if (info.event.id) {
                    window.location.href = `/events/detail/${info.event.id}`;
                }
            }
        });
        calendar.render();

        const addEventBtn = document.getElementById('addEventBtn');
        if (addEventBtn) {
            addEventBtn.addEventListener('click', function () {
                const today = new Date().toISOString().split('T')[0];
                window.location.href = `/events/create?date=${today}`;
            });
        }
    }

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
