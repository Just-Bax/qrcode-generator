--At the end of installation process we lock all the components package to prevent modification to the configuration

declare
    c_component_package_name constant components_package.name%type := 'Use your package name here';
begin
    update components_package set is_locked = 1 where name = c_component_package_name;
    dbms_output.put_line('The [' || c_component_package_name || '] components package is locked');
end;