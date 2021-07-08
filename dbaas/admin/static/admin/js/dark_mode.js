var isDark = localStorage.getItem('darkmode');

var setDarkMode = function(){
    console.log('add dark')
    django.jQuery('body').addClass('dark')
}

var removeDarkMode = function(){
    console.log('remove dark')
    django.jQuery('body').removeClass('dark')
}


if (!isDark)
    isDark = false;

if (isDark){
    setDarkMode();
}

localStorage.setItem('darkmode', isDark);


django.jQuery(document).ready(function(){
    django.jQuery('#dmodechckbox').attr('checked', 'checked');
    django.jQuery('#dmodechckbox').on("change", function(v){
        isDark = django.jQuery('#dmodechckbox').is(':checked');
        if (isDark){
            setDarkMode();
        }else{
            removeDarkMode();
        }
        localStorage.setItem('darkmode', isDark);
    });
})

