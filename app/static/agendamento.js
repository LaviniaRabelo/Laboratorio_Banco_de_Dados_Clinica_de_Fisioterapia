function normalizeText(value) {
    return (value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
}

function formatDateInput(input) {
    const digits = input.value.replace(/\D/g, '').slice(0, 8);
    let formatted = digits;
    if (digits.length > 2) { formatted = `${digits.slice(0, 2)}/${digits.slice(2)}`; }
    if (digits.length > 4) { formatted = `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`; }
    input.value = formatted;
}

function formatCpfInput(input) {
    const digits = input.value.replace(/\D/g, '').slice(0, 11);
    let formatted = digits;
    if (digits.length > 3) { formatted = `${digits.slice(0, 3)}.${digits.slice(3)}`; }
    if (digits.length > 6) { formatted = `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`; }
    if (digits.length > 9) { formatted = `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`; }
    input.value = formatted;
}

function setupAutocomplete(container) {
    const input = container.querySelector('[data-autocomplete-input]');
    const results = container.querySelector('[data-autocomplete-results]');
    const hidden = document.getElementById(input.dataset.hiddenTarget);
    const options = Array.from(results.querySelectorAll('.autocomplete-option'));
    function closeResults() { results.hidden = true; }
    function choose(option) {
        hidden.value = option.dataset.id;
        input.value = option.dataset.label;
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
        closeResults();
    }
    function renderMatches() {
        const query = normalizeText(input.value.trim());
        let visibleCount = 0;
        options.forEach((option) => {
            const matches = query.length === 0 || normalizeText(option.dataset.search).includes(query);
            const shouldShow = matches && visibleCount < 8;
            option.hidden = !shouldShow;
            if (shouldShow) { visibleCount += 1; }
        });
        results.hidden = visibleCount === 0;
    }
    input.addEventListener('focus', renderMatches);
    input.addEventListener('input', () => {
        hidden.value = '';
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
        renderMatches();
    });
    options.forEach((option) => { option.addEventListener('click', () => choose(option)); });
    document.addEventListener('click', (event) => { if (!container.contains(event.target)) { closeResults(); } });
    if (hidden.value) {
        const selected = options.find((option) => option.dataset.id === hidden.value);
        if (selected) { input.value = selected.dataset.label; }
    }
}

function filterProceduresByPhysio() {
    const physioId = document.getElementById('id_fisioterapeuta')?.value || '';
    const physioOptions = Array.from(document.querySelectorAll('#physio_results .autocomplete-option'));
    const selectedPhysio = physioOptions.find((option) => option.dataset.id === physioId);
    const specialties = new Set((selectedPhysio?.dataset.specialties || '').split(',').map((value) => value.trim()).filter(Boolean));
    const procedureOptions = Array.from(document.querySelectorAll('[data-procedure-option]'));
    const help = document.getElementById('procedure-help');
    const empty = document.getElementById('procedure-empty');
    let visibleCount = 0;
    let selectionChanged = false;
    procedureOptions.forEach((option) => {
        const checkbox = option.querySelector('input[name="procedimentos"]');
        const procedureSpecialty = String(option.dataset.specialty || '');
        const compatible = Boolean(selectedPhysio) && specialties.has(procedureSpecialty);
        option.hidden = !compatible;
        option.style.display = compatible ? 'flex' : 'none';
        if (checkbox) {
            checkbox.disabled = !compatible;
            if (!compatible && checkbox.checked) { checkbox.checked = false; selectionChanged = true; }
        }
        if (compatible) { visibleCount += 1; }
    });
    if (!selectedPhysio) {
        if (help) { help.textContent = 'Selecione um fisioterapeuta para ver somente os procedimentos que ele pode realizar.'; }
        if (empty) { empty.hidden = true; }
    } else if (visibleCount === 0) {
        if (help) { help.textContent = 'Este fisioterapeuta não possui procedimentos compatíveis cadastrados.'; }
        if (empty) { empty.hidden = false; }
    } else {
        if (help) {
            const name = selectedPhysio.dataset.label?.split(' — ')[0] || 'o fisioterapeuta';
            help.textContent = `${visibleCount} procedimento(s) disponível(is) para ${name}.`;
        }
        if (empty) { empty.hidden = true; }
    }
    if (selectionChanged) {
        const dateInput = document.getElementById('data_atendimento');
        const timeInput = document.getElementById('hora_inicio');
        if (dateInput) { dateInput.value = ''; }
        if (timeInput) { timeInput.value = ''; }
    }
    refreshAvailabilityButton();
}

function selectedDuration() {
    return Array.from(document.querySelectorAll('input[name="procedimentos"]:checked')).reduce((total, checkbox) => total + Number(checkbox.dataset.duration || 0), 0);
}
function isoMonth(date) { const year = date.getFullYear(); const month = String(date.getMonth() + 1).padStart(2, '0'); return `${year}-${month}`; }
function ptDate(isoDate) { const [year, month, day] = isoDate.split('-'); return `${day}/${month}/${year}`; }
function parsePtDate(value) { const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value || ''); return match ? `${match[3]}-${match[2]}-${match[1]}` : null; }
function monthLabel(date) { const label = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(date); return label.charAt(0).toUpperCase() + label.slice(1); }
function sameMonth(a, b) { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth(); }
function firstAllowedMonth() { const now = new Date(); return new Date(now.getFullYear(), now.getMonth(), 1); }
function lastAllowedMonth() { const now = new Date(); const limit = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 180); return new Date(limit.getFullYear(), limit.getMonth(), 1); }
let visibleMonth = firstAllowedMonth();
let availabilityCache = null;
let selectedIsoDate = null;

function refreshAvailabilityButton() {
    const physio = document.getElementById('id_fisioterapeuta')?.value || '';
    const room = document.getElementById('id_sala')?.value || '';
    const duration = selectedDuration();
    const button = document.getElementById('open-calendar');
    const help = document.getElementById('availability-help');
    if (!button || !help) { return; }
    const missing = [];
    if (!physio) { missing.push('fisioterapeuta'); }
    if (!room) { missing.push('sala'); }
    if (duration <= 0) { missing.push('procedimento'); }
    button.disabled = missing.length > 0;
    help.textContent = missing.length > 0 ? `Falta selecionar: ${missing.join(', ')}.` : `Pronto para consultar. Duração total: ${duration} minutos.`;
}

async function loadAvailability() {
    const physio = document.getElementById('id_fisioterapeuta').value;
    const room = document.getElementById('id_sala').value;
    const duration = selectedDuration();
    const status = document.getElementById('calendar-status');
    if (!physio || !room || duration <= 0) { throw new Error('Selecione fisioterapeuta, sala e pelo menos um procedimento antes de consultar o calendário.'); }
    status.textContent = 'Consultando disponibilidade...';
    const params = new URLSearchParams({ mes: isoMonth(visibleMonth), id_fisioterapeuta: physio, id_sala: room, duracao: String(duration) });
    const response = await fetch(`/api/agendamentos/disponibilidade?${params.toString()}`, { headers: { Accept: 'application/json' } });
    let data;
    try { data = await response.json(); } catch (_error) { throw new Error('O servidor não retornou uma resposta válida para o calendário.'); }
    if (!response.ok) { throw new Error(data.erro || 'Não foi possível consultar a disponibilidade.'); }
    availabilityCache = data;
    renderCalendar();
    status.textContent = `Duração considerada: ${data.duracao_minutos} minutos.`;
}

function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    const title = document.getElementById('calendar-title');
    const previous = document.getElementById('previous-month');
    const next = document.getElementById('next-month');
    grid.replaceChildren();
    title.textContent = monthLabel(visibleMonth);
    previous.disabled = sameMonth(visibleMonth, firstAllowedMonth());
    next.disabled = sameMonth(visibleMonth, lastAllowedMonth());
    const firstDay = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
    for (let i = 0; i < firstDay.getDay(); i += 1) { const empty = document.createElement('span'); empty.className = 'calendar-empty'; grid.appendChild(empty); }
    for (const day of availabilityCache.dias) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = day.disponivel ? 'calendar-day available' : 'calendar-day unavailable';
        button.textContent = String(Number(day.data.slice(-2)));
        button.dataset.date = day.data;
        button.disabled = !day.disponivel;
        button.title = day.disponivel ? `${day.horarios.length} horário(s) disponível(is)` : 'Sem horário disponível';
        if (day.data === selectedIsoDate) { button.classList.add('selected'); }
        if (day.disponivel) { button.addEventListener('click', () => selectDay(day)); }
        grid.appendChild(button);
    }
}

function selectDay(day) {
    selectedIsoDate = day.data;
    renderCalendar();
    const section = document.getElementById('time-section');
    const title = document.getElementById('selected-day-title');
    const buttons = document.getElementById('time-buttons');
    section.hidden = false;
    title.textContent = `Horários disponíveis em ${ptDate(day.data)}`;
    buttons.replaceChildren();
    for (const time of day.horarios) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'time-button';
        button.textContent = time;
        button.addEventListener('click', () => chooseDateTime(day.data, time));
        buttons.appendChild(button);
    }
}

function chooseDateTime(isoDate, time) {
    document.getElementById('data_atendimento').value = ptDate(isoDate);
    document.getElementById('hora_inicio').value = time;
    document.getElementById('availability-dialog').close();
    updateInsuranceOptions();
}

async function openCalendar() {
    const dialog = document.getElementById('availability-dialog');
    const status = document.getElementById('calendar-status');
    const timeSection = document.getElementById('time-section');
    const grid = document.getElementById('calendar-grid');
    visibleMonth = firstAllowedMonth(); selectedIsoDate = null; availabilityCache = null;
    timeSection.hidden = true; grid.replaceChildren(); status.textContent = ''; dialog.showModal();
    try { await loadAvailability(); } catch (error) { status.textContent = error.message; }
}

function shiftMonth(delta) {
    const candidate = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + delta, 1);
    if (candidate < firstAllowedMonth() || candidate > lastAllowedMonth()) { return; }
    visibleMonth = candidate; selectedIsoDate = null;
    document.getElementById('time-section').hidden = true;
    loadAvailability().catch((error) => { document.getElementById('calendar-status').textContent = error.message; });
}

function updateInsuranceOptions() {
    const patientId = document.getElementById('id_paciente')?.value || '';
    const select = document.getElementById('id_convenio');
    const area = document.getElementById('insurance-area');
    const empty = document.getElementById('insurance-empty');
    const mode = document.querySelector('input[name="tipo_atendimento"]:checked');
    if (!select || !area || !mode) { return; }
    const isInsurance = mode.value === 'convenio';
    const paymentSection = document.getElementById('payment-section');
    area.hidden = !isInsurance;
    select.disabled = !isInsurance;
    if (paymentSection) { paymentSection.hidden = isInsurance; }
    if (isInsurance) {
        const pending = document.querySelector('input[name="situacao_pagamento"][value="pendente"]');
        const paymentMethod = document.getElementById('id_forma_pagamento');
        if (pending) { pending.checked = true; }
        if (paymentMethod) { paymentMethod.value = ''; paymentMethod.disabled = true; paymentMethod.required = false; }
    }
    if (!isInsurance) { select.value = ''; if (empty) { empty.hidden = true; } updatePaymentOptions(); return; }
    const appointmentIsoDate = parsePtDate(document.getElementById('data_atendimento')?.value || '');
    const today = new Date();
    const fallbackDate = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, '0'), String(today.getDate()).padStart(2, '0')].join('-');
    const referenceDate = appointmentIsoDate || fallbackDate;
    let visibleCount = 0;
    Array.from(select.options).forEach((option) => {
        if (!option.value) { option.hidden = false; return; }
        const samePatient = option.dataset.patient === patientId;
        const start = option.dataset.start || '0000-01-01';
        const end = option.dataset.end || '9999-12-31';
        const activeOnDate = start <= referenceDate && referenceDate <= end;
        const show = samePatient && activeOnDate;
        option.hidden = !show; option.disabled = !show;
        if (show) { visibleCount += 1; }
    });
    const selected = select.options[select.selectedIndex];
    if (selected && selected.value && selected.hidden) { select.value = ''; }
    if (empty) { empty.hidden = visibleCount > 0; }
}

function updatePaymentOptions() {
    const situation = document.querySelector('input[name="situacao_pagamento"]:checked');
    const area = document.getElementById('payment-method-area');
    const select = document.getElementById('id_forma_pagamento');
    if (!situation || !area || !select) { return; }
    const isPaid = situation.value === 'pago';
    area.hidden = !isPaid; select.disabled = !isPaid; select.required = isPaid;
    if (!isPaid) { select.value = ''; }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-autocomplete]').forEach(setupAutocomplete);
    document.querySelectorAll('.date-mask').forEach((input) => { input.addEventListener('input', () => formatDateInput(input)); formatDateInput(input); });
    ['qp_cpf', 'qf_cpf'].forEach((id) => { const input = document.getElementById(id); if (input) { input.addEventListener('input', () => formatCpfInput(input)); } });
    document.getElementById('id_paciente')?.addEventListener('change', () => { updateInsuranceOptions(); });
    document.getElementById('id_fisioterapeuta')?.addEventListener('change', () => { filterProceduresByPhysio(); });
    document.getElementById('id_sala')?.addEventListener('change', () => { refreshAvailabilityButton(); });
    document.querySelectorAll('input[name="procedimentos"]').forEach((checkbox) => { checkbox.addEventListener('change', () => { refreshAvailabilityButton(); document.getElementById('data_atendimento').value = ''; document.getElementById('hora_inicio').value = ''; }); });
    document.querySelectorAll('input[name="tipo_atendimento"]').forEach((radio) => { radio.addEventListener('change', updateInsuranceOptions); });
    document.querySelectorAll('input[name="situacao_pagamento"]').forEach((radio) => { radio.addEventListener('change', updatePaymentOptions); });
    document.getElementById('open-calendar')?.addEventListener('click', openCalendar);
    document.getElementById('close-calendar')?.addEventListener('click', () => { document.getElementById('availability-dialog').close(); });
    document.getElementById('previous-month')?.addEventListener('click', () => { shiftMonth(-1); });
    document.getElementById('next-month')?.addEventListener('click', () => { shiftMonth(1); });
    document.getElementById('availability-dialog')?.addEventListener('click', (event) => { if (event.target.id === 'availability-dialog') { event.target.close(); } });
    filterProceduresByPhysio();
    refreshAvailabilityButton();
    updateInsuranceOptions();
    updatePaymentOptions();
});
