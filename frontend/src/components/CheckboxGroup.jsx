export default function CheckboxGroup({ legend, options, selectedValues, onToggle }) {
  return (
    <fieldset>
      <legend>{legend}</legend>
      <div className="option-grid">
        {options.map((option) => (
          <label className="checkbox-option" key={option.value}>
            <input
              type="checkbox"
              checked={selectedValues.includes(option.value)}
              onChange={() => onToggle(option.value)}
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
