/**
 * AI Interview S2 — 조건 자동 배정 + 녹음 파일 수집
 *
 * 구글 계정 하나로 동작합니다. 카드 등록·별도 서버 없음.
 *  · 배정 기록 → 구글 스프레드시트
 *  · 녹음 파일 → 구글 드라이브 폴더
 *
 * 설치 방법은 backend/README.md 참고.
 */

/* ══════════ 설정 ══════════ */
// 이미 만들어 둔 시트·폴더 ID 입니다. 그대로 두시면 됩니다.
const SHEET_ID  = '1mD3lP4jtQiDVYcUeQ6VJ_Br1i0qh9nthAOHOZ4UoZu0';  // AI면접_배정기록
const FOLDER_ID = '1QWtun8uh4Ow9lJMFcAx536DSJHVwP7fr';             // AI면접_녹음

/* 배정 버킷
   분석용 조건 코드는 C1~C6 그대로 유지하고,
   Single(1명) 조건은 페르소나 3종을 하위 버킷으로 둠려 균등 배정한다.
   즉 셀은 6개, 배정 버킷은 3×3 + 3 = 12개.
   Multi(3명) 는 문항별로 세 페르소나가 고정 등장하므로 persona 는 빈 값. */
const PERSONAS = ['middle_man', 'young_woman', 'young_man'];

const CONDITIONS = [];
[{ code:'C1', form:'x' }, { code:'C2', form:'avatar' }, { code:'C3', form:'human' }]
  .forEach(function (c) {
    PERSONAS.forEach(function (p) {
      CONDITIONS.push({ code:c.code, agents:1, form:c.form, persona:p });
    });
  });
[{ code:'C4', form:'x' }, { code:'C5', form:'avatar' }, { code:'C6', form:'human' }]
  .forEach(function (c) {
    CONDITIONS.push({ code:c.code, agents:3, form:c.form, persona:'' });
  });

const bucketKey = c => c.code + '|' + (c.persona || '');

const TARGET_PER_CELL = 25;   // 조건당 목표 인원 (참고용, 초과해도 배정은 계속됨)

/* ══════════ 엔드포인트 ══════════ */
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.action === 'assign') return json(assign(body));
    if (body.action === 'upload') return json(upload(body));
    if (body.action === 'log')    return json(saveLog(body));
    if (body.action === 'name')   return json(setName(body));
    return json({ ok:false, error:'unknown action' });
  } catch (err) {
    return json({ ok:false, error:String(err) });
  }
}

function doGet() {
  return json({ ok:true, message:'AI Interview S2 backend' });
}

/* ══════════ 1. 조건 배정 ══════════
   동시 접속에도 인원이 어긋나지 않도록 락을 걸고 처리합니다.

   같은 사람은 몇 번을 다시 들어와도 처음 받은 번호·조건을 그대로 받습니다.
   같은 사람인지는 "이름 + 휴대전화 뒷 4자리"로 판단합니다 (로그인 때 함께 보냄).
   브라우저가 기억하는 번호만으로는 부족합니다 — 다른 브라우저·시크릿 창·다른 기기로
   다시 들어오면 번호가 없어서 새 조건을 받고 동명이인(홍길동B)으로 처리되기 때문입니다.
   (웹앱은 접속자 IP 를 볼 수 없어 IP 로는 구분하지 못합니다.) */
function normName(v)  { return String(v == null ? '' : v).trim().replace(/\s+/g, ' '); }
function normPhone(v) {
  const d = String(v == null ? '' : v).replace(/\D/g, '');
  return d ? ('0000' + d).slice(-4) : '';
}
// 시트의 이름은 동명이인 구분용 알파벳이 붙어 있을 수 있다 (홍길동, 홍길동B …)
function nameRegex(raw) {
  const esc = raw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp('^' + esc + '([A-Z])?$');
}
function resumed(r) {
  const saved = String(r[6] || '');
  const per = PERSONAS.indexOf(saved) >= 0 ? saved : '';   // 구버전 행 보호
  const c = CONDITIONS.find(x => x.code === r[3] && (x.agents === 3 || x.persona === per)) ||
            CONDITIONS.find(x => x.code === r[3]);
  return { ok:true, participant_id:r[1], condition:c.code,
           agents:c.agents, form:c.form, persona:c.persona || '', resumed:true };
}

function assign(body) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet('assignments');
    const rows = sh.getDataRange().getValues();   // [시각, 번호, 이름, 조건, 면접관수, 형태, 페르소나, 브라우저, 순번, 뒷4자리]

    const name  = normName(body.name);
    const phone = normPhone(body.phone4);
    const known = !!(name && phone);              // 이름·뒷4자리를 함께 보냈는가
    const re    = known ? nameRegex(name) : null;
    const hasCond = r => CONDITIONS.some(x => x.code === r[3]);          // 마커 행 제외
    const isSame  = r => known && normPhone(r[9]) === phone && re.test(normName(r[2]));
    const isBlank = r => !normName(r[2]) && !normPhone(r[9]);

    // 1) 같은 사람이 이미 배정돼 있으면 그 배정을 돌려준다 (여러 번이면 가장 먼저 받은 것).
    if (known) {
      for (let i = 1; i < rows.length; i++) {
        if (hasCond(rows[i]) && isSame(rows[i])) return resumed(rows[i]);
      }
    }

    // 2) 브라우저가 기억하는 번호. 그 행이 비어 있거나 본인 것일 때만 이어 간다.
    //    다른 사람 이름이 적혀 있으면(한 기기를 여럿이 쓰는 경우) 새 참가자로 배정한다.
    if (body.participant_id) {
      for (let i = 1; i < rows.length; i++) {
        if (rows[i][1] === body.participant_id && hasCond(rows[i])) {
          if (!known || isBlank(rows[i]) || isSame(rows[i])) return resumed(rows[i]);
          break;
        }
      }
    }

    // 버킷별 현재 인원 (코드 + 페르소나)
    const count = {};
    CONDITIONS.forEach(c => count[bucketKey(c)] = 0);
    for (let i = 1; i < rows.length; i++) {
      const saved = String(rows[i][6] || '');
      const per = PERSONAS.indexOf(saved) >= 0 ? saved : '';
      const k = rows[i][3] + '|' + per;
      if (count[k] !== undefined) count[k]++;
    }

    // 가장 적은 버킷들 중 무작위
    const min = Math.min.apply(null, CONDITIONS.map(c => count[bucketKey(c)]));
    const pool = CONDITIONS.filter(c => count[bucketKey(c)] === min);
    const picked = pool[Math.floor(Math.random() * pool.length)];

    // 번호는 항상 시트의 다음 번호. 브라우저가 보낸 번호가 시트에 없으면(테스트 때 저장된
    // 번호 등) 쓰지 않는다 — 그대로 쓰면 P1005 처럼 순서에서 벗어난 번호가 생긴다.
    const pid = nextPid(rows);
    sh.appendRow([new Date(), pid, '', picked.code, picked.agents, picked.form,
                  picked.persona || '', body.ua || '', min + 1, '']);
    // 이름·뒷4자리를 배정과 동시에 적는다 — 다시 들어왔을 때 같은 사람인지 알아보는 열쇠.
    if (known) {
      const row = sh.getLastRow();
      sh.getRange(row, 3).setValue(uniqueName(rows, -1, name));
      sh.getRange(row, 10).setNumberFormat('@').setValue(phone);
    }

    return { ok:true, participant_id:pid, condition:picked.code,
             agents:picked.agents, form:picked.form,
             persona:picked.persona || '', resumed:false,
             counts:count, target:TARGET_PER_CELL };
  } finally {
    lock.releaseLock();
  }
}

/* 로그인 시 이름과 휴대전화 뒷 4자리를 배정 시트의 해당 참가자 행에 채웁니다.
   같은 이름이 이미 있으면 뒤에 알파벳을 붙여 시트에서 구분합니다.
     홍길동 → (두 번째) 홍길동B → (세 번째) 홍길동C …
   먼저 들어온 사람의 이름은 그대로 두므로, 이미 내보낸 자료와 어긋나지 않습니다.
   (뒷 4자리까지 같으면 같은 사람이므로 assign 이 새 행을 만들지 않습니다.)
   selfRow 가 -1 이면 아직 시트에 없는 새 행의 이름을 정한다. */
function uniqueName(rows, selfRow, raw) {
  const re = nameRegex(raw);

  // 이 행에 이미 확정된 이름이 있으면 그대로 둔다.
  // (재접속할 때마다 새로 계산하면 다른 사람과 같은 글자를 받을 수 있다)
  if (selfRow >= 0) {
    const cur = normName(rows[selfRow][2]);
    if (cur && re.test(cur)) return cur;
  }

  let n = 0;
  for (let i = 1; i < rows.length; i++) {
    if (i === selfRow) continue;
    if (re.test(normName(rows[i][2]))) n++;
  }
  if (n === 0) return raw;
  return n <= 25 ? raw + String.fromCharCode(65 + n)   // B, C, … Z
                 : raw + (n + 1);                      // 26명을 넘기면 숫자로
}

function setName(body) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet('assignments');
    const rows = sh.getDataRange().getValues();

    // 예전에 만들어진 시트에는 '뒷4자리' 칸이 없으므로 한 번만 채워 넣는다
    if (!String(rows[0] && rows[0][9] || '').trim()) {
      sh.getRange(1, 10).setValue('뒷4자리');
    }

    const raw    = String(body.name || '').trim().replace(/\s+/g, ' ');
    const phone4 = String(body.phone4 || '').replace(/\D/g, '').slice(0, 4);

    for (let i = 1; i < rows.length; i++) {
      if (rows[i][1] === body.participant_id) {
        const name = raw ? uniqueName(rows, i, raw) : '';
        sh.getRange(i + 1, 3).setValue(name);
        // 텍스트 서식으로 써야 '0123' 의 앞자리 0 이 사라지지 않는다 (숫자로 저장되면 123 이 된다)
        sh.getRange(i + 1, 10).setNumberFormat('@').setValue(phone4);
        return { ok:true, name:name, phone4:phone4 };
      }
    }
    return { ok:false, error:'participant not found' };
  } finally {
    lock.releaseLock();
  }
}

function nextPid(rows) {
  let max = 0;
  for (let i = 1; i < rows.length; i++) {
    const m = String(rows[i][1]).match(/^P(\d+)$/);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return 'P' + String(max + 1).padStart(4, '0');
}

/* ══════════ 2. 녹음 업로드 ══════════
   파일은 participant_id 별 하위 폴더에 저장됩니다. */
function upload(body) {
  const root = DriveApp.getFolderById(FOLDER_ID);
  const pid  = body.participant_id || 'unknown';
  let dir;
  const it = root.getFoldersByName(pid);
  dir = it.hasNext() ? it.next() : root.createFolder(pid);

  const bytes = Utilities.base64Decode(body.data);
  const blob  = Utilities.newBlob(bytes, body.mime || 'audio/webm', body.filename);
  const file  = dir.createFile(blob);

  sheet('uploads').appendRow([new Date(), pid, body.participant_name || '',
                              body.condition || '', body.persona || '',
                              body.question || '', body.filename,
                              Math.round(file.getSize() / 1024) + 'KB']);
  return { ok:true, file_id:file.getId() };
}

/* ══════════ 3. 진행 로그 ══════════
   한 세션에 90~110 줄이 들어옵니다. appendRow 는 한 줄마다 시트를 왕복하므로
   그만큼이면 1분을 넘깁니다. 범위를 잡아 setValues 로 한 번에 씁니다.
   appendRow 와 달리 "마지막 줄 읽기 → 쓰기"가 한 동작이 아니므로 락이 필요합니다.
   락이 없으면 두 참가자가 동시에 끝날 때 같은 줄에 써서 한쪽 로그가 덮어써집니다. */
function saveLog(body) {
  const rows = body.rows || [];
  if (!rows.length) return { ok:true, saved:0 };
  const cell = v => (v === undefined || v === null) ? '' : v;
  const values = rows.map(r =>
    [cell(r.t), cell(r.pid), cell(r.name), cell(r.cond), cell(r.q), cell(r.event), cell(r.extra)]);

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet('logs');
    const start = sh.getLastRow() + 1;
    const short = start + values.length - 1 - sh.getMaxRows();
    if (short > 0) sh.insertRowsAfter(sh.getMaxRows(), short);   // 시트 끝을 넘으면 줄을 먼저 늘린다
    sh.getRange(start, 1, values.length, values[0].length).setValues(values);
    return { ok:true, saved:values.length };
  } finally {
    lock.releaseLock();
  }
}

/* ══════════ 유틸 ══════════ */
function sheet(name) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    const head = {
      assignments: ['시각','참가자','이름','조건','면접관수','형태','페르소나','브라우저','배정순번','뒷4자리'],
      uploads:     ['시각','참가자','이름','조건','페르소나','문항','파일명','크기'],
      logs:        ['시각','참가자','이름','조건','문항','이벤트','비고']
    }[name];
    if (head) sh.appendRow(head);
  }
  return sh;
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
                       .setMimeType(ContentService.MimeType.JSON);
}

/* ══════════ 배정 현황 확인용 (에디터에서 직접 실행) ══════════ */
function 현황보기() {
  const rows = sheet('assignments').getDataRange().getValues();
  const count = {};
  CONDITIONS.forEach(c => count[bucketKey(c)] = 0);
  for (let i = 1; i < rows.length; i++) {
    const saved = String(rows[i][6] || '');
    const per = PERSONAS.indexOf(saved) >= 0 ? saved : '';
    const k = rows[i][3] + '|' + per;
    if (count[k] !== undefined) count[k]++;
  }
  Logger.log('총 %s명', rows.length - 1);
  CONDITIONS.forEach(c =>
    Logger.log('%s (%s명 %s %s) : %s명', c.code, c.agents, c.form,
               c.persona || '-', count[bucketKey(c)]));
}
