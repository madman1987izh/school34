// В static/js/app.js
document.addEventListener('DOMContentLoaded', function() {
  // Валидация форм
  const forms = document.querySelectorAll('.needs-validation');
  forms.forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  // Подсветка текущего дня
  const today = new Date().getDay();
  if (today > 0 && today < 7) {
    document.querySelectorAll(`td:contains('${days[today-1]}')`).forEach(td => {
      td.classList.add('table-warning');
    });
  }
});