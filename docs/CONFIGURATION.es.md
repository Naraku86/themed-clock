# Configuración e integración

[English](CONFIGURATION.md) · [README](../README.es.md)

## Configuración

El archivo es opcional. Desde la raíz del proyecto, crea una copia propia;
conserva tu configuración anterior si ya existe:

```sh
mkdir -p ~/.config/themed-clock
cp config.ini.example ~/.config/themed-clock/config.ini
```

`--config RUTA` selecciona otro archivo; si no existe, muestra un error.
`--theme NOMBRE` tiene prioridad y se conserva al pulsar `R`. Una recarga inválida
mantiene los ajustes anteriores y muestra un mensaje breve. Las opciones desconocidas
del INI se ignoran; los valores inválidos de opciones conocidas muestran un error.

| Opción | Valor inicial | Función |
| --- | --- | --- |
| `theme` | `auto` | Tema seleccionado o fuente de tema del escritorio. |
| `theme_file` | vacío | Archivo con un nombre de tema o enlace a su directorio. |
| `font` | `auto` | `compact`, `arrakis`, `megastructure`, `serif`. |
| `style` | `auto` | `blocks`, `light`, `ascii`: relleno de los números. |
| `color` | `auto` | Color del tema o `#RRGGBB`; depende de la paleta de la terminal. |
| `max_scale` | `3` | Escala máxima entre 1 y 6. |
| `seconds_min_width` | `54` | Ancho mínimo de segundos; en detallado también necesita 78. |
| `blink_colon` | `yes` | Alterna los separadores cada segundo; `no` los mantiene fijos. |
| `animations` | `yes` | Activar o desactivar: `yes` / `no`. |
| `animation` | `auto` | Efecto del tema, `none` o nombre explícito. |
| `animation_interval` | `180` | Segundos desde que termina un efecto hasta el siguiente. |
| `animation_duration` | `8` | Duración del efecto, entre 2 y 30 segundos. |
| `worm_min_width` | `64` | Ancho mínimo solo para el gusano opcional. |
| `worm_min_height` | `16` | Alto mínimo solo para el gusano opcional. |

Efectos: `sandstorm`, `worm`, `construction`, `energy`, `data`, `forge`, `orbits`,
`hourglass`, `wired`, `magi`, `pulse`. `signal` es un alias de construcción.
La tormenta y el gusano requieren Dune; la construcción requiere BLAME!.
`style=ascii` cambia solo los números; las animaciones siguen usando Unicode.

## Tamaños

Los números crecen por niveles de 5/10/15 filas en compacto o 7/14/21 en detallado,
según ancho, alto y `max_scale`. El detallado necesita al menos 50 columnas y siete
filas. Los segundos necesitan 54 columnas en compacto o 78 en detallado; si no,
se ocultan. La fecha necesita una fila de separación y no desplaza el reloj.
En ventanas diminutas se usa texto HH:MM. La tipografía y transparencia reales
pertenecen a la terminal; el programa controla el dibujo de caracteres.

## Seguir el tema del escritorio

`theme=auto` consulta `THEMED_CLOCK_THEME`, después `theme_file` y finalmente usa
Minimal. La variable se hereda al iniciar; para cambios en vivo, usa un archivo o
enlace. Un archivo de texto puede contener un nombre como `blame`.

Para los dotfiles de Edgar, configura `theme_file=~/.config/temas-terminal/actual`.
Ese enlace es opcional; no se incluyen dotfiles personales. `fundacion` y
`mundodisco` son alias de `foundation` y `discworld`.

## Inicio automático

En Hyprland con configuración Lua:

```lua
hl.on("hyprland.start", function()
    hl.exec_cmd("kitty --class themed-clock -o window_padding_width=4 ~/.local/bin/themed-clock")
end)
```

En Sway:

```text
exec kitty --class themed-clock -o window_padding_width=4 ~/.local/bin/themed-clock
```

Adapta el ejemplo a tu configuración existente. Referencias:
[Hyprland](https://github.com/hyprwm/Hyprland/blob/main/example/hyprland.lua) y
[Sway](https://github.com/swaywm/sway/blob/master/sway/sway.5.scd).
La posición, reglas flotantes, fuente y opacidad se configuran en el escritorio o
terminal. La instalación no modifica barras, fondos ni configuración de terminal.

## Pruebas y vista previa

```sh
make test
~/.local/bin/themed-clock --theme foundation --preview 78 18 --animate
```

El primer efecto automático empieza a los 20 segundos. `S`/`W` lo activa al instante.
`Q`/`Esc`/`Ctrl+C` sale restaurando la terminal. Si Unicode se ve irregular, prueba
una fuente monoespaciada adecuada o `style=ascii` con `animation=none`.

## Regenerar los GIFs

Herramientas opcionales de desarrollo: Pillow y una fuente Unicode monoespaciada.
Ejecuta `python3 scripts/render_previews.py --font /ruta/fuente.ttf`; sin `--font`
usa `fc-match monospace` de Fontconfig. No son dependencias de ejecución.
