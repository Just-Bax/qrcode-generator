--It is important to activate rules after rebuilding Objrefs and importing PL/SQL packages
--This sample script also validates rules before activation

declare
    c_component_package_name constant components_package.name%type := 'Use your package name here';

    cursor cur_rules_by_comp_package(p_comp_package in components_package.name%type) is
        select rule.rule_id, rule.rule, rule.sql_text, rule.rule_class_id
          from rule
          join comp_pkg_object_xref cpx on cpx.object_id = rule.rule_id
          join components_package cp on cp.components_package_id = cpx.components_package_id
         where cpx.component_id = pkg_audit_comp.c_rule_component_id
           and cp.name = p_comp_package;
begin
    for rec_rule in cur_rules_by_comp_package(c_component_package_name) loop
        dbms_output.put_line('Enabling rule [' ||  rec_rule.rule || ']' || pkg_str.c_lb);
        
        if rec_rule.rule_class_id = pkg_ruleator.c_class_plsql then
            pkg_ruleator.compile_rule_plsql_block_and_raise(rec_rule.sql_text);
        end if;
        
        update rule set is_enabled = 1 where rule_id = rec_rule.rule_id;
        
        commit;
    end loop;
end;
