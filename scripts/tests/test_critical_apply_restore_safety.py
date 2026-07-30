#!/usr/bin/env python3
from __future__ import annotations
import os, shutil, socket, stat, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'scripts'))
from critical_apply_filesystem import *
from critical_apply_restore import make_boundary

class RestoreSafetyTest(unittest.TestCase):
    group='path_archive_filetype_safety'
    def setUp(self): self.tmp=Path(tempfile.mkdtemp(prefix='m3-safe-')); self.root=self.tmp/'root'; self.root.mkdir(); (self.root/'a').write_text('a')
    def tearDown(self): shutil.rmtree(self.tmp,ignore_errors=True)
    def test_good_relative(self): self.assertEqual(validate_relative_path('a/b.txt'),'a/b.txt')
    def test_absolute_rejected(self): self.assertRaises(FilesystemSafetyError,validate_relative_path,'/x')
    def test_dotdot_rejected(self): self.assertRaises(FilesystemSafetyError,validate_relative_path,'a/../b')
    def test_empty_rejected(self): self.assertRaises(FilesystemSafetyError,validate_relative_path,'')
    def test_backslash_normalized(self): self.assertEqual(validate_relative_path('a\\b'),'a/b')
    def test_depth_limit(self): self.assertRaises(FilesystemSafetyError,validate_relative_path,'/'.join(['x']*40),max_depth=5)
    def test_length_limit(self): self.assertRaises(FilesystemSafetyError,validate_relative_path,'x'*300,max_length=10)
    def test_resolve_under_ok(self): self.assertTrue(str(resolve_under(self.root,'a')).endswith('/a'))
    def test_resolve_under_escape(self): self.assertRaises(FilesystemSafetyError,resolve_under,self.root,'../x')
    def test_root_symlink_rejected(self): link=self.tmp/'link'; link.symlink_to(self.root); self.assertRaises(FilesystemSafetyError,real_dir,link,label='ROOT')
    def test_inventory_regular_ok(self): self.assertEqual(inventory_tree(self.root)['file_count'],1)
    def test_inventory_dir_count(self): self.assertEqual(inventory_tree(self.root)['directory_count'],0)
    def test_inventory_hash_stable(self): self.assertEqual(inventory_tree(self.root)['inventory_sha256'],inventory_tree(self.root)['inventory_sha256'])
    def test_symlink_rejected(self): (self.root/'l').symlink_to('a'); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root)
    def test_hardlink_rejected(self): os.link(self.root/'a',self.root/'b'); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root)
    def test_fifo_rejected(self): os.mkfifo(self.root/'fifo'); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root)
    def test_socket_rejected(self): s=socket.socket(socket.AF_UNIX); p=self.root/'sock'; s.bind(str(p)); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root); s.close()
    def test_setuid_rejected(self): os.chmod(self.root/'a',0o4755); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root)
    def test_duplicate_unicode_collision(self): (self.root/'A').write_text('x'); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root)
    def test_file_count_limit(self): b=Boundary('b',str(self.root),('a',),('.',),(),(),max_file_count=0); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root,boundary=b)
    def test_byte_limit(self): b=Boundary('b',str(self.root),('a',),('.',),(),(),max_logical_bytes=0); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root,boundary=b)
    def test_individual_size_limit(self): b=Boundary('b',str(self.root),('a',),('.',),(),(),max_individual_file_size=0); self.assertRaises(FilesystemSafetyError,inventory_tree,self.root,boundary=b)
    def test_write_allowed_declared_path(self): b=Boundary('b',str(self.root),('a',),('a',),(),()); assert_write_allowed(b,'a')
    def test_write_broad_dot_rejected(self): b=Boundary('b',str(self.root),('a',),('.',),(),()); self.assertRaises(FilesystemSafetyError,assert_write_allowed,b,'a')
    def test_write_forbidden(self): b=Boundary('b',str(self.root),('a',),('a',),('a',),()); self.assertRaises(FilesystemSafetyError,assert_write_allowed,b,'a')
    def test_write_outside(self): b=Boundary('b',str(self.root),('a',),('a',),(),()); self.assertRaises(FilesystemSafetyError,assert_write_allowed,b,'b')
    def test_boundary_digest_sha(self): b=Boundary('b',str(self.root),('a',),('a',),(),()); self.assertEqual(len(boundary_digest(b)),64)
    def test_same_filesystem(self): self.assertIsInstance(ensure_same_filesystem(self.root,self.tmp),int)
    def test_compare_inventory_true(self): i=inventory_tree(self.root); self.assertTrue(compare_inventories(i,i))
    def test_compare_inventory_false(self): i=inventory_tree(self.root); (self.root/'b').write_text('b'); self.assertFalse(compare_inventories(i,inventory_tree(self.root)))
    def test_stable_copy(self): dst=self.tmp/'copy/a'; out=stable_file_copy(self.root/'a',dst,root=self.root); self.assertEqual(out['sha256'],sha256_file(dst))
    def test_stable_copy_no_symlink(self): l=self.root/'link'; l.symlink_to('a'); self.assertRaises(Exception,stable_file_copy,l,self.tmp/'x',root=self.root)
    def test_type_regular(self): self.assertEqual(classify_filetype(self.root/'a'),'regular')
    def test_type_directory(self): self.assertEqual(classify_filetype(self.root),'directory')

UNSAFE=['/abs','../x','x/../../y','.','', 'a//b', 'a/..', 'a/'+('x'*300)]
for i,path in enumerate(UNSAFE):
    def make(p):
        def test(self): self.assertFalse(is_relative_safe(p))
        return test
    setattr(RestoreSafetyTest,f'test_unsafe_path_case_{i}',make(path))

if __name__=='__main__': unittest.main(verbosity=2)
