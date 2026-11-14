import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const sourceDir = process.env.EPISTEMICS_REVIEW_SOURCE ?? fileURLToPath(new URL('.', import.meta.url));
const outputDir = process.env.EPISTEMICS_REVIEW_OUTPUT ?? path.resolve('outputs', 'revisao-humana-20261114');
const rows = JSON.parse(await fs.readFile(`${sourceDir}/blind.json`, 'utf8'));
assert.equal(rows.length, 64);
const workbook = Workbook.create();
const sheet = workbook.worksheets.add('Revisao');
sheet.showGridLines = false;
sheet.tabColor = '#344B71';
const first = 12;
const last = first + rows.length - 1;
sheet.getRange(`A1:F${last}`).format = {
  font: { name: 'Arial', size: 11, color: '#263244' },
  verticalAlignment: 'top',
};
for (const [column, width] of [['A', 15], ['B', 48], ['C', 34], ['D', 44], ['E', 22], ['F', 31]]) {
  sheet.getRange(`${column}1:${column}${last}`).format.columnWidth = width;
}
sheet.getRange('A1:F1').format.rowHeight = 8;
sheet.getRange('A2').values = [['Revisão humana das respostas']];
sheet.getRange('A2').format.font = { name: 'Arial', size: 16, bold: true, color: '#21344E' };
sheet.getRange('A2:F2').format.rowHeight = 26;
sheet.getRange('A3:F3').format.rowHeight = 8;
sheet.getRange('A4:F4').values = [['Revisor', null, null, 'Classificados', null, 'de 64']];
sheet.getRange('E4').formulas = [[`=64-COUNTBLANK(E${first}:E${last})`]];
sheet.getRange('A5:B5').values = [['Data', null]];
sheet.getRange('B5').setNumberFormat('yyyy-mm-dd');
sheet.getRange('B4:B5').format.fill = '#FFF0C7';
sheet.getRange('A4:F5').format.rowHeight = 22;
sheet.getRange('A6:F6').format.rowHeight = 7;
sheet.getRange('A7').values = [['Na coluna E, escolhe o número da opção que a resposta exprime. Usa INDETERMINADA quando a escolha for insuficiente ou ambígua.']];
sheet.getRange('A8').values = [['Na coluna F, podes transcrever outro resultado explícito. Julga o que a resposta diz, sem resolver o problema.']];
sheet.getRange('A9').values = [['Regista as decisões antes de consultar soluções oficiais ou outras avaliações. Cada leitor preenche a sua cópia.']];
sheet.getRange('A7:F9').format.wrapText = false;
sheet.getRange('A7:F9').format.rowHeight = 20;
sheet.getRange('A10:F10').format.rowHeight = 8;
sheet.getRange('A11:F11').values = [['Caso', 'Pergunta', 'Opções apresentadas', 'Resposta a interpretar', 'Opção identificada', 'Outro resultado explícito (opcional)']];
sheet.getRange('A11:F11').format = {
  fill: '#344B71',
  font: { name: 'Arial', size: 11, color: '#FFFFFF', bold: true },
  verticalAlignment: 'center',
  horizontalAlignment: 'center',
  wrapText: true,
  rowHeight: 34,
};
function literal(text) {
  return text.startsWith('=') ? `'${text}` : text;
}
const matrix = rows.map(row => [row.id, literal(row.question),
  row.options.map((option, index) => `${index + 1}) ${option}`).join('\n'),
  literal(row.archived_reply), null, null]);
sheet.getRange(`A${first}:F${last}`).values = matrix;
sheet.getRange(`A${first}:D${last}`).format.wrapText = true;
sheet.getRange(`E${first}:F${last}`).format = { fill: '#FFF5DA', wrapText: true };
sheet.getRange(`E${first}:E${last}`).format.horizontalAlignment = 'center';
sheet.getRange(`A${first}:A${last}`).setNumberFormat('@');
sheet.getRange(`F${first}:F${last}`).setNumberFormat('@');
for (const [index, row] of rows.entries()) {
  const lineCount = (text, width) => text.split('\n').reduce((n, line) => n + Math.max(1, Math.ceil(line.length / width)), 0);
  const height = Math.max(82, 19 * Math.max(lineCount(row.question, 43), lineCount(matrix[index][2], 30), lineCount(row.archived_reply, 39)) + 18);
  const excelRow = first + index;
  sheet.getRange(`A${excelRow}:F${excelRow}`).format.rowHeight = height;
  if (index % 2 === 1) sheet.getRange(`A${excelRow}:D${excelRow}`).format.fill = '#F2F5F8';
  sheet.getRange(`E${excelRow}`).dataValidation = { rule: { type: 'list', values: [...row.options.map((_, i) => String(i + 1)), 'INDETERMINADA'] } };
}
sheet.freezePanes.freezeRows(11);
// Exercise the input-driven progress count, then restore every reader field.
sheet.getRange('E12').values = [['INDETERMINADA']];
workbook.recalculate();
assert.equal(sheet.getRange('E4').values[0][0], 1);
sheet.getRange('E12').clear({ applyTo: 'contents' });
workbook.recalculate();
assert.equal(sheet.getRange('E4').values[0][0], 0);
assert.ok(sheet.getRange(`E${first}:F${last}`).values.every(row => row.every(value => value === null || value === '')));
const check = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 12 }, maxChars: 500 });
console.log(check.ndjson);
await fs.mkdir(outputDir, { recursive: true });
const preview = await workbook.render({ sheetName: 'Revisao', range: 'A1:F15', scale: 1.35, format: 'png' });
await fs.writeFile(`${outputDir}/review-preview.png`, new Uint8Array(await preview.arrayBuffer()));
const file = await SpreadsheetFile.exportXlsx(workbook);
await file.save(`${outputDir}/Revisao_humana_64_casos.xlsx`);
console.log(JSON.stringify({ file: `${outputDir}/Revisao_humana_64_casos.xlsx`, cases: rows.length, reader_fields_blank: true, progress: 0 }));
