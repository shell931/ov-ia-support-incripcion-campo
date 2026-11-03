import { CLOSE_REASONS, CLOSE_REASON_LABELS, DESTINATION_LABELS, formatWaiting } from './labels';

describe('labels', () => {
  it('maps every destination to Spanish', () => {
    expect(DESTINATION_LABELS.help_desk).toBe('Mesa de ayuda');
    expect(DESTINATION_LABELS.census_office).toBe('Dirección de Censo');
    expect(DESTINATION_LABELS.logistics).toBe('Logística');
  });

  it('has a label for each close reason', () => {
    expect(CLOSE_REASONS.length).toBe(4);
    for (const r of CLOSE_REASONS) expect(CLOSE_REASON_LABELS[r]).toBeTruthy();
  });

  it('formats waiting time', () => {
    expect(formatWaiting(5)).toBe('5 min');
    expect(formatWaiting(60)).toBe('1 h');
    expect(formatWaiting(125)).toBe('2 h 5 min');
  });
});
