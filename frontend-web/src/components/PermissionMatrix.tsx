import { addPermissions, permissionGroups, permissionPresets } from '../permissions';

interface PermissionMatrixProps {
  value: string[];
  onChange: (permissions: string[]) => void;
  disabled?: boolean;
}

export function PermissionMatrix({ value, onChange, disabled }: PermissionMatrixProps) {
  return (
    <fieldset disabled={disabled} className="space-y-3 border-t border-slate-200 pt-3">
      <legend className="font-bold text-sm text-slate-800">Permissões / Módulos Liberados</legend>
      <p className="text-xs text-slate-600">Perfis adicionam módulos; combine ou ajuste as seleções livremente.</p>
      <div className="flex flex-wrap gap-2">
        {permissionPresets.map((preset) => (
          <button key={preset.label} type="button" onClick={() => onChange(addPermissions(value, preset.permissions))}
            className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-700 disabled:opacity-50">
            {preset.label}
          </button>
        ))}
      </div>
      {permissionGroups.map((group) => (
        <div key={group.title}>
          <p className="mb-1 text-xs font-bold text-slate-600">{group.title}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {group.items.map((permission) => (
              <label key={permission.id} className="flex items-center gap-2 text-xs text-slate-700">
                <input type="checkbox" checked={value.includes(permission.id)}
                  onChange={(event) => onChange(event.target.checked
                    ? addPermissions(value, [permission.id])
                    : value.filter((item) => item !== permission.id))} />
                {permission.label}
              </label>
            ))}
          </div>
        </div>
      ))}
    </fieldset>
  );
}
