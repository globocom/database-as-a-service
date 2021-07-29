var isDark = localStorage.getItem('darkmode');
isDark = (isDark === "true" || isDark === true)

var setDarkMode = function(){
    console.log('add dark')
    django.jQuery('body').addClass('dark')
    django.jQuery('#dmodechckbox').attr('checked', 'checked');
}

var removeDarkMode = function(){
    console.log('remove dark')
    django.jQuery('body').removeClass('dark')
    django.jQuery('#dmodechckbox').removeAttr('checked');
}

if (!isDark)
    isDark = false;

if (isDark){
    setDarkMode();
}else{
    removeDarkMode();
}

localStorage.setItem('darkmode', isDark);


django.jQuery(document).ready(function(){
    django.jQuery('#dmodechckbox').on("change", function(v){
        isDark = django.jQuery('#dmodechckbox').is(':checked');
        if (isDark){
            setDarkMode();
        }else{
            removeDarkMode();
        }

        console.log('setting', isDark)
        localStorage.setItem('darkmode', isDark);
    });
})

