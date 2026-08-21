import sys
import warnings

# Устанавливаем фильтр ДО импорта любых модулей
if not sys.warnoptions:
    sys.warnoptions = ['ignore::DeprecationWarning']