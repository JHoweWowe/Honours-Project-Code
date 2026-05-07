new TomSelect('#include-input', {
    create: true,
    createOnBlur: true,
    persist: false,
    delimiter: ',',
    plugins: ['remove_button'],
    onItemAdd: function() {
        this.setTextboxValue('');
        this.refreshOptions();
    }
});

new TomSelect('#exclude-input', {
    create: true,
    createOnBlur: true,
    persist: false,
    delimiter: ',',
    plugins: ['remove_button'],
    onItemAdd: function() {
        this.setTextboxValue('');
        this.refreshOptions();
    }
});
