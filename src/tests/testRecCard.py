import test # get ../lib/ in path
import gglobals
import time, gtk
gglobals.gourmetdir = '/tmp/'
gglobals.dbargs['file'] = '/tmp/recipes.db'

import GourmetRecipeManager
from reccard import add_with_undo

def add_save_and_check (rc, lines_groups_and_dc):
    added = []
    for l,g,dc in lines_groups_and_dc:
        # add_with_undo is what's called by any of the ways a user can add an ingredient.
        add_with_undo(
            rc,
            lambda *args: added.append(rc.add_ingredient_from_line(l,group_iter=g))
            )
    #print 'add_save_and_check UNDO HISTORY:',rc.history
    added = [rc.ingtree_ui.ingController.get_persistent_ref_from_iter(i) for i in added]
    rc.saveEditsCB()
    ings = rc.rd.get_ings(rc.current_rec)
    check_ings([i[2] for i in lines_groups_and_dc],ings)
    #print 'add_save_and_check.return:',lines_groups_and_dc,'->',added
    return added

def check_ings (check_dics,ings):
    """Given a list of dictionaries of properties to check and
    ingredients, check that our ingredients have those properties.  We
    assume our check_dics refer to the last ingredients in the list
    ings
    """
    n = -1
    check_dics.reverse()
    for dic in check_dics:
        ings[n]
        for k,v in dic.items():
            try:
                assert(getattr(ings[n],k)==v)
            except AssertionError:
                #print 'Failed assertion',n,k,v,ings[n]
                #print 'We are looking for: '
                #for d in check_dics: print ' ',d
                #print 'in:'
                #for a,u,i in [(i.amount,i.unit,i.item) for i in ings]: print ' ',a,u,i
                #print 'we are at ',n,ings[n].amount,ings[n],ings[n].unit,ings[n].item
                #print 'we find ',k,'=',getattr(ings[n],k),'instead of ',v
                raise
        n -= 1

def test_ing_editing (rc, verbose=True):
    """Handed a recipe card, test ingredient editing"""
    # Add some ingredients in a group...
    rc.show_edit(tab=rc.NOTEBOOK_ING_PAGE)        
    g = rc.ingtree_ui.ingController.add_group('Foo bar')
    if verbose: print "Testing ingredient editing - add 4 ingredients to a group."
    add_save_and_check(
        rc,
        [['1 c. sugar',g,
         {'amount':1,'unit':'c.','item':'sugar','inggroup':'Foo bar'}
         ],
        ['1 c. silly; chopped and sorted',g,
         {'amount':1,'unit':'c.','ingkey':'silly','inggroup':'Foo bar'},
         ],
        ['1 lb. very silly',g,
         {'amount':1,'unit':'lb.','item':'very silly','inggroup':'Foo bar'},
         ],
        ['1 tbs. extraordinarily silly',g,
         {'amount':1,'unit':'tbs.','item':'extraordinarily silly','inggroup':'Foo bar'}
         ],]
        )
    if verbose: print "Ingredient editing successful"
    return g
    
def test_ing_undo (rc, verbose=True):
    rc.show_edit(tab=rc.NOTEBOOK_ING_PAGE)        
    ings_groups_and_dcs = [
        # Just 1 ing -- more will require more undos
        ['1 c. oil',None,{'amount':1,'unit':'c.','item':'oil'}]
        ] 
    refs = add_save_and_check(
        rc,
        ings_groups_and_dcs
        )
    #print 'refs',refs,
    #print '->',[rc.ingtree_ui.ingController.get_iter_from_persistent_ref(r)
    #            for r in refs]
    rc.ingtree_ui.ingController.delete_iters(
        *[rc.ingtree_ui.ingController.get_iter_from_persistent_ref(r)
         for r in refs]
        )
    #print 'test_ing_undo - just deleted - UNDO HISTORY:',rc.history
    # Saving our edits...
    rc.saveEditsCB()
    try:
        ii = rc.rd.get_ings(rc.current_rec)
        check_ings(
            [i[2] for i in ings_groups_and_dcs],
            ii
            )
    except AssertionError:
        if verbose: print 'Deletion worked!' # we expect an assertion error
    else:
        if verbose: print [i[2] for i in ings_groups_and_dcs]
        if verbose: print 'corresponds to'
        if verbose: print [(i.amount,i.unit,i.item) for i in ii]
        raise "Ings Not Deleted!"
    # Undo after save...
    rc.undo.emit('activate') # Undo deletion
    #print 'test_ing_undo - just pressed undo - UNDO HISTORY:',rc.history
    rc.saveEditsCB()
    # Check that our ingredients have been put back properly by the undo action!
    #print 'Checking for ',[i[2] for i in ings_groups_and_dcs]
    #print 'Checking in ',rc.rd.get_ings(rc.current_rec)
    check_ings(
        [i[2] for i in ings_groups_and_dcs],
        rc.rd.get_ings(rc.current_rec)
        )
    if verbose: print 'Undeletion worked!'

def test_undo_save_sensitivity (rc, verbose=True):
    rc.show_edit(tab=rc.NOTEBOOK_ATTR_PAGE)        
    rc.saveEditsCB()
    try:
        assert(not rc.save.get_sensitive())
    except:
        print 'FAILURE: SAVE Button not properly desensitized after save'; raise
    else:
        if verbose: print 'SAVE Button properly desensitized'
    for widget,value in [('rating',8),
                         ('preptime',30*60),
                         ('cooktime',60*60),
                         ('title','Foo bar'),
                         ('cuisine','Mexican'),
                         ('category','Entree')                         
                         ]:
        if verbose: print 'TESTING ',widget
        if type(value)==int:
            orig_value = rc.rw[widget].get_value()
            rc.rw[widget].set_value(value)
            get_method = rc.rw[widget].get_value
            if verbose: print 'Set with set_value(',value,')'
        elif widget in rc.reccom:
            orig_value = rc.rw[widget].entry.get_text()
            rc.rw[widget].entry.set_text(value)
            get_method = rc.rw[widget].entry.get_text
            if verbose: print 'Set with entry.set_text(',value,')'            
        else:
            orig_value = rc.rw[widget].get_text()
            rc.rw[widget].set_text(value)
            get_method = rc.rw[widget].get_text
            if verbose: print 'Set with set_text(',value,')'                        
        try: assert(get_method()==value)
        except: print '''Value not set properly for %s
        is %s, should be %s'''%(
            widget,get_method(),value
            ); raise
        try:
            assert(rc.save.get_sensitive())
        except:
            print 'Save not sensitized after setting %s'%widget; raise
        else:
            if verbose: print 'Save sensitized properly after setting %s'%widget
        rc.undo.emit('activate')
        if orig_value and type(value)!=int: rc.undo.emit('activate') # Blank text, then fill it
        try:
            assert(get_method()==orig_value)
        except:
            print '''Value not unset properly on for %s
            Should have been set to %s'''%(widget,orig_value); raise
        else:
            if verbose: print 'Value set properly for %s after Undo'%widget
        try:
            assert(not rc.save.get_sensitive())
        except:
            print 'Save not desensitized after unsetting %s'%widget; raise
        else:
            if verbose: print 'Save desensitized correctly after unsetting %s'%widget
        rc.redo.emit('activate')
        if orig_value and type(value)!=int: rc.redo.emit('activate') # Blank text, then fill it        
        try: assert(get_method()==value)
        except: print '''Value not set properly for REDO %s
        is %s, should be %s'''%(
            widget,get_method(),value
            ); raise
        try:
            assert(rc.save.get_sensitive())
        except:
            print 'Save not sensitized after setting %s via REDO'%widget; raise
        rc.undo.emit('activate')
        if orig_value and type(value)!=int: rc.undo.emit('activate') # Blank text, then fill it
        try:
            assert(get_method()==orig_value)
        except:
            print '''Value not unset properly on for %s UNDO->REDO->UNDO
            Should have been set to %s'''%(widget,orig_value); raise
        else:
            if verbose: print 'Value set properly for %s after Undo->Redo->Undo'%widget
        try:
            assert(not rc.save.get_sensitive())
        except:
            print 'Save not desensitized after undo->redo->undo %s'%widget; raise
        else:
            if verbose: print 'Save desensitized correctly after undo->redo->undo %s'%widget

rg = GourmetRecipeManager.RecGui()
rg.newRecCard()
while gtk.events_pending(): gtk.main_iteration()
rec_id,rec_card = rg.rc.items()[0]

try:
    test_ing_editing(rec_card,verbose=False)
    print 'Ing Editing works!'
    test_ing_undo(rec_card,verbose=False)
    print 'Ing Undo works!'
    test_undo_save_sensitivity(rec_card,verbose=False)
    print 'Undo properly sensitizes save widget.'
except:
    import traceback; traceback.print_exc()
    gtk.main()
else:
    rec_card.hide()
    
    