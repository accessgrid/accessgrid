from AccessGrid import CertificateRepository 

repo = CertificateRepository.CertificateRepository('repo')

name = [("O", "test"),
        ("OU", "here"),
        ("CN", "bob")]
desc = repo.CreateCertificateRequest(name, "asdfasdf")
print desc.ExportPEM()
print "subj is ", desc.GetSubject()
print "mod is ", desc.GetModulus()
print "modhash is ", desc.GetModulusHash()
